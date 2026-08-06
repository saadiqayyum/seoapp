"""
AI Video Analysis & Improved Script Generator
LangGraph agent that transcribes, analyzes, and synthesizes educational video content
into a new, original, high-quality video script.
"""

import os
import re
import tempfile
import subprocess
from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    # ── Inputs ──────────────────────────────────────────────────────────────
    topic: Optional[str]           # may be None → inferred from video content
    video_urls: List[str]          # 1–3 URLs
    desired_duration: str          # e.g. "5 minutes", "30 seconds"
    target_audience: str           # Beginner / Intermediate / Advanced
    tone: str                      # Professional / Conversational / etc.
    output_language: str           # e.g. "English", "Spanish"

    # ── Intermediate ────────────────────────────────────────────────────────
    transcripts: List[Dict]        # [{url, transcript_text, source, error}]
    video_analyses: List[str]      # per-video analysis text
    cross_analysis: str            # comparative synthesis
    teaching_plan: str             # structured plan for the new video
    production_notes: str          # visual / production suggestions

    # ── Output ──────────────────────────────────────────────────────────────
    final_script: str              # the polished narration script
    final_output: str              # complete formatted report
    error: Optional[str]           # non-fatal warnings accumulated during run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm(temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o",
        temperature=temperature,
        api_key=os.environ["OPENAI_API_KEY"],
    )


def _extract_youtube_id(url: str) -> Optional[str]:
    """Return the 11-char YouTube video ID from any common YouTube URL format."""
    patterns = [
        r"(?:youtube\.com/watch\?(?:.*&)?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def _parse_duration_words(duration_str: str) -> int:
    """Convert a plain-text duration to an approximate word count (150 wpm)."""
    s = duration_str.lower()
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return 300  # default: 2 minutes
    num = float(m.group(1))
    if "second" in s or "sec" in s:
        minutes = num / 60.0
    else:
        minutes = num
    return max(50, int(minutes * 150))


def _truncate(text: str, max_chars: int = 14000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[… transcript truncated for length …]"


# ---------------------------------------------------------------------------
# Node 1 — Extract Transcripts
# ---------------------------------------------------------------------------

def extract_transcripts(state: AgentState) -> dict:
    """
    For each URL:
      1. Try YouTube Transcript API (fastest, no audio download needed).
      2. Fall back to yt-dlp audio download → OpenAI Whisper transcription.
    """
    transcripts: List[Dict] = []
    warnings: List[str] = []

    for url in state["video_urls"]:
        entry: Dict[str, Any] = {
            "url": url,
            "transcript_text": "",
            "source": "none",
            "error": None,
        }

        # ── Attempt 1: YouTube Transcript API ─────────────────────────────
        video_id = _extract_youtube_id(url)
        if video_id:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

                # Try the default language first, then any available language
                try:
                    items = YouTubeTranscriptApi.get_transcript(video_id)
                except Exception:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    # Prefer manually created, then auto-generated
                    t = None
                    for candidate in transcript_list:
                        t = candidate
                        break
                    if t is None:
                        raise NoTranscriptFound(video_id, [], {})
                    items = t.fetch()

                entry["transcript_text"] = " ".join(i["text"] for i in items)
                entry["source"] = "youtube_transcript_api"
                entry["video_id"] = video_id
                transcripts.append(entry)
                continue

            except Exception as yt_err:
                warnings.append(f"YouTube Transcript API failed for {url}: {yt_err}")

        # ── Attempt 2: yt-dlp + OpenAI Whisper ────────────────────────────
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_out = os.path.join(tmpdir, "audio.%(ext)s")
                result = subprocess.run(
                    [
                        "yt-dlp",
                        "-x",
                        "--audio-format", "mp3",
                        "--audio-quality", "5",
                        "-o", audio_out,
                        "--no-playlist",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                audio_file = os.path.join(tmpdir, "audio.mp3")
                if result.returncode != 0 or not os.path.exists(audio_file):
                    raise RuntimeError(f"yt-dlp exit {result.returncode}: {result.stderr[:300]}")

                import openai as _openai
                client = _openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
                with open(audio_file, "rb") as f:
                    resp = client.audio.transcriptions.create(model="whisper-1", file=f)
                entry["transcript_text"] = resp.text
                entry["source"] = "whisper"
        except Exception as wb_err:
            entry["error"] = str(wb_err)
            warnings.append(f"yt-dlp/Whisper failed for {url}: {wb_err}")

        transcripts.append(entry)

    combined_warnings = "; ".join(warnings) if warnings else None
    return {"transcripts": transcripts, "error": combined_warnings}


# ---------------------------------------------------------------------------
# Node 2 — Analyze Each Video
# ---------------------------------------------------------------------------

def analyze_videos(state: AgentState) -> dict:
    """Run a structured LLM analysis on each video's transcript."""
    llm = _llm(temperature=0.3)
    analyses: List[str] = []

    for i, t in enumerate(state["transcripts"], start=1):
        url = t["url"]
        text = t.get("transcript_text", "")

        if not text:
            err = t.get("error", "No transcript available")
            analyses.append(
                f"## Analysis of Video {i}\n**URL:** {url}\n\n"
                f"⚠️ Could not extract transcript: {err}"
            )
            continue

        prompt = f"""You are an expert educational content analyst.

Analyze the following transcript from an educational video and provide a comprehensive breakdown.

**Video {i} URL:** {url}

**Transcript:**
{_truncate(text)}

---
Provide your analysis using exactly these headings:

### 1. Main Topic
### 2. Key Concepts (bulleted list)
### 3. Explanation Structure
### 4. Teaching Style
### 5. Important Examples & Demonstrations
### 6. Analogies Used
### 7. Strengths
### 8. Weaknesses
### 9. Missing Concepts
### 10. Areas That Could Be Explained More Clearly

Be specific, critical, and thorough."""

        resp = llm.invoke([HumanMessage(content=prompt)])
        analyses.append(f"## Video {i} Analysis\n**URL:** {url}\n\n{resp.content}")

    return {"video_analyses": analyses}


# ---------------------------------------------------------------------------
# Node 3 — Cross-Video Analysis
# ---------------------------------------------------------------------------

def cross_video_analysis(state: AgentState) -> dict:
    """Compare all video analyses and synthesize a unified understanding."""
    llm = _llm(temperature=0.3)
    n = len(state["video_analyses"])
    combined = "\n\n---\n\n".join(state["video_analyses"])
    topic_hint = f"User-specified topic: **{state['topic']}**" if state.get("topic") else "No topic specified — infer from content."

    prompt = f"""You are a senior instructional designer tasked with synthesizing analyses from {n} educational video(s).

{topic_hint}

---
{combined}
---

Produce a detailed **Cross-Video Comparative Analysis** covering:

### 1. Inferred / Confirmed Topic
### 2. Common Concepts (appear in multiple videos)
### 3. Unique Insights Per Video (valuable information found only in each)
### 4. Best Explanations Across All Videos (and which video provides them)
### 5. Contradictions or Discrepancies
### 6. Collective Knowledge Gaps (important concepts missing from ALL videos)
### 7. Unified Topic Understanding (synthesized complete picture)
### 8. Key Opportunities for Improvement

This analysis will be used to create a superior new educational video script."""

    resp = llm.invoke([HumanMessage(content=prompt)])
    return {"cross_analysis": resp.content}


# ---------------------------------------------------------------------------
# Node 4 — Build Teaching Plan
# ---------------------------------------------------------------------------

def build_teaching_plan(state: AgentState) -> dict:
    """Design an optimised, audience-appropriate teaching plan."""
    llm = _llm(temperature=0.4)
    topic_line = state.get("topic") or "the topic identified from analysis"

    prompt = f"""You are an expert instructional designer creating the blueprint for a new educational video.

**Topic:** {topic_line}
**Target Audience:** {state['target_audience']}
**Desired Duration:** {state['desired_duration']}
**Tone:** {state['tone']}
**Output Language:** {state['output_language']}

**Cross-Video Analysis:**
{state['cross_analysis']}

---
Design a structured teaching plan that outlines exactly how the new video should work.
Include:

### 1. Video Title (engaging, SEO-friendly)
### 2. Learning Objectives (what viewers will know/be able to do after watching)
### 3. Opening Hook Strategy (how to grab attention in the first 10 seconds)
### 4. Section Breakdown
For each section include:
  - Section name
  - Core concepts to cover
  - Recommended example or analogy
  - Estimated time allocation
### 5. Concept Ordering Rationale (why this sequence is optimal)
### 6. Audience Adaptations (how to pitch it for {state['target_audience']} learners)
### 7. Tone & Language Guidance (how to maintain {state['tone']} tone)
### 8. Closing Summary Strategy

Allocate total time to match {state['desired_duration']}. Be specific and actionable."""

    resp = llm.invoke([HumanMessage(content=prompt)])
    return {"teaching_plan": resp.content}


# ---------------------------------------------------------------------------
# Node 5 — Generate Script
# ---------------------------------------------------------------------------

def generate_script(state: AgentState) -> dict:
    """Write the complete, original, polished narration script."""
    llm = _llm(temperature=0.8)
    topic_line = state.get("topic") or "the topic identified from analysis"
    target_words = _parse_duration_words(state["desired_duration"])

    prompt = f"""You are a world-class educational video script writer.

**Topic:** {topic_line}
**Target Audience:** {state['target_audience']}
**Desired Duration:** {state['desired_duration']} (~{target_words} spoken words at 150 wpm)
**Tone:** {state['tone']}
**Output Language:** {state['output_language']}

**Teaching Plan to Follow:**
{state['teaching_plan']}

---
## SCRIPT REQUIREMENTS

1. Write approximately **{target_words} words** of narration.
2. Label every section with a heading and a timestamp marker, e.g.:
   `## [Hook] [0:00–0:15]`
3. Write entirely in **{state['output_language']}**.
4. Use a **{state['tone']}** tone appropriate for **{state['target_audience']}** learners.
5. **Do NOT copy or closely paraphrase** any source video — synthesize and create original content.
6. Optimise for **spoken delivery**: natural rhythm, clear sentence structure, meaningful pauses (mark with `[PAUSE]` where helpful).
7. Use smooth transitions between sections.
8. Start with a compelling hook.
9. End with a concise, memorable summary that reinforces the key takeaways.
10. If the topic benefits from analogies or examples, include them naturally in the narration.

---
Write the complete script now. Output ONLY the script (no meta-commentary).

Begin:"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    return {"final_script": resp.content}


# ---------------------------------------------------------------------------
# Node 6 — Generate Production Notes
# ---------------------------------------------------------------------------

def generate_production_notes(state: AgentState) -> dict:
    """Generate contextual visual and production suggestions for the script."""
    llm = _llm(temperature=0.5)
    topic_line = state.get("topic") or "the topic identified from analysis"

    prompt = f"""You are a video production consultant reviewing an educational video script.

**Topic:** {topic_line}
**Target Audience:** {state['target_audience']}
**Duration:** {state['desired_duration']}
**Tone:** {state['tone']}

**Script:**
{_truncate(state['final_script'], max_chars=8000)}

---
Provide concise, practical **Production Suggestions** organised under these headings:

### 🎨 Visual Style & On-Screen Graphics
### 📸 B-Roll & Background Footage Ideas
### 📊 Diagrams, Charts & Animations
### 💻 Code Snippets / Screen Recordings (if applicable)
### 🎬 Chapter Titles for Video Platform Chapters
### 🎵 Music & Audio Tone
### ✂️ Editing Rhythm & Pacing Tips
### ♿ Accessibility Recommendations

Keep suggestions practical and specific to this script's content."""

    resp = llm.invoke([HumanMessage(content=prompt)])
    return {"production_notes": resp.content}


# ---------------------------------------------------------------------------
# Node 7 — Format Output
# ---------------------------------------------------------------------------

def format_output(state: AgentState) -> dict:
    """Assemble the complete, structured final report."""

    script = state.get("final_script", "")
    word_count = len(script.split())
    total_seconds = int(word_count / 150 * 60)
    est_min = total_seconds // 60
    est_sec = total_seconds % 60

    topic_display = state.get("topic") or "Inferred from video content"

    lines: List[str] = []

    # ── Header ───────────────────────────────────────────────────────────────
    lines += [
        "# 🎬 AI Video Analysis & Improved Script Generator",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| **Topic** | {topic_display} |",
        f"| **Target Audience** | {state['target_audience']} |",
        f"| **Requested Duration** | {state['desired_duration']} |",
        f"| **Tone** | {state['tone']} |",
        f"| **Language** | {state['output_language']} |",
        "",
    ]

    # ── Videos Analyzed ──────────────────────────────────────────────────────
    lines += ["---", "## 📹 Videos Analyzed", ""]
    for i, t in enumerate(state.get("transcripts", []), start=1):
        ok = "✅" if t.get("transcript_text") else "❌"
        src = t.get("source", "—")
        lines.append(f"{i}. {ok} `{t['url']}` *(transcribed via {src})*")
    lines.append("")

    # ── Section 1: Video Summaries ────────────────────────────────────────────
    lines += ["---", "## 1. Video Summaries", ""]
    for analysis in state.get("video_analyses", []):
        lines.append(analysis)
        lines.append("")

    # ── Section 2: Comparative Analysis ──────────────────────────────────────
    lines += ["---", "## 2. Comparative Analysis", "", state.get("cross_analysis", ""), ""]

    # ── Section 3: Improved Content Structure ────────────────────────────────
    lines += ["---", "## 3. Improved Content Structure", "", state.get("teaching_plan", ""), ""]

    # ── Section 4: Final Script ───────────────────────────────────────────────
    lines += ["---", "## 4. Final Video Script", "", script, ""]

    # ── Section 5: Duration Estimate ─────────────────────────────────────────
    lines += [
        "---",
        "## 5. Estimated Duration",
        "",
        f"- **Script word count:** ~{word_count:,} words",
        f"- **Estimated runtime:** ~{est_min}:{est_sec:02d} (at 150 words/minute average speaking pace)",
        f"- **Requested duration:** {state['desired_duration']}",
        "",
    ]

    # ── Section 6: Production Suggestions ────────────────────────────────────
    lines += ["---", "## 6. Production Suggestions", "", state.get("production_notes", ""), ""]

    # ── Warnings ─────────────────────────────────────────────────────────────
    if state.get("error"):
        lines += [
            "---",
            "## ⚠️ Processing Warnings",
            "",
            state["error"],
            "",
        ]

    return {"final_output": "\n".join(lines)}


# ---------------------------------------------------------------------------
# Graph Assembly
# ---------------------------------------------------------------------------

def build_graph():
    wf = StateGraph(AgentState)

    wf.add_node("extract_transcripts", extract_transcripts)
    wf.add_node("analyze_videos", analyze_videos)
    wf.add_node("cross_video_analysis", cross_video_analysis)
    wf.add_node("build_teaching_plan", build_teaching_plan)
    wf.add_node("generate_script", generate_script)
    wf.add_node("generate_production_notes", generate_production_notes)
    wf.add_node("format_output", format_output)

    wf.add_edge(START, "extract_transcripts")
    wf.add_edge("extract_transcripts", "analyze_videos")
    wf.add_edge("analyze_videos", "cross_video_analysis")
    wf.add_edge("cross_video_analysis", "build_teaching_plan")
    wf.add_edge("build_teaching_plan", "generate_script")
    wf.add_edge("generate_script", "generate_production_notes")
    wf.add_edge("generate_production_notes", "format_output")
    wf.add_edge("format_output", END)

    return wf.compile()


graph = build_graph()

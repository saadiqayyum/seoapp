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


def _build_proxy_config():
    """
    Build the correct youtube-transcript-api v1.x ProxyConfig object and a
    plain proxy URL string for yt-dlp, based on environment variables.

    Priority:
      1. WEBSHARE_PROXY_USERNAME + WEBSHARE_PROXY_PASSWORD
         → WebshareProxyConfig (rotating residential, best for YouTube)
      2. YOUTUBE_PROXY_URL  (e.g. http://user:pass@host:port)
         → GenericProxyConfig

    Returns (ytt_proxy_config, ytdlp_proxy_url) — either may be None.
    """
    from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig

    ws_user = os.environ.get("WEBSHARE_PROXY_USERNAME")
    ws_pass = os.environ.get("WEBSHARE_PROXY_PASSWORD")
    if ws_user and ws_pass:
        ytt_cfg = WebshareProxyConfig(
            proxy_username=ws_user,
            proxy_password=ws_pass,
            retries_when_blocked=5,
        )
        # Construct the Webshare rotating-proxy URL for yt-dlp
        ytdlp_url = f"http://{ws_user}:{ws_pass}@p.webshare.io:80"
        return ytt_cfg, ytdlp_url

    generic_url = (
        os.environ.get("YOUTUBE_PROXY_URL")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("HTTP_PROXY")
    )
    if generic_url:
        ytt_cfg = GenericProxyConfig(https_url=generic_url, http_url=generic_url)
        return ytt_cfg, generic_url

    return None, None


# ---------------------------------------------------------------------------
# Node 1 — Extract Transcripts
# ---------------------------------------------------------------------------

def _supadata_fetch(url: str, api_key: str) -> str:
    """
    Fetch transcript via Supadata API (cloud-IP-safe, no proxy needed).
    Handles both synchronous (HTTP 200) and asynchronous (HTTP 202 + polling) responses.
    Raises RuntimeError on failure.
    """
    import requests as _req
    import time

    resp = _req.get(
        "https://api.supadata.ai/v1/transcript",
        params={"url": url, "text": "true"},
        headers={"x-api-key": api_key},
        timeout=30,
    )

    # Synchronous result
    if resp.status_code == 200:
        data = resp.json()
        content = data.get("content", "")
        if isinstance(content, list):
            return " ".join(seg.get("text", "") for seg in content)
        return str(content)

    # Async job — poll until done (max ~2 minutes)
    if resp.status_code == 202:
        job_id = resp.json().get("jobId")
        if not job_id:
            raise RuntimeError("Supadata returned 202 but no jobId")
        for _ in range(60):
            time.sleep(2)
            poll = _req.get(
                f"https://api.supadata.ai/v1/transcript/{job_id}",
                headers={"x-api-key": api_key},
                timeout=30,
            )
            if poll.status_code != 200:
                continue
            result = poll.json()
            status = result.get("status")
            if status == "completed":
                content = result.get("content", "")
                if isinstance(content, list):
                    return " ".join(seg.get("text", "") for seg in content)
                return str(content)
            if status == "failed":
                raise RuntimeError(f"Supadata job failed: {result.get('error')}")
        raise RuntimeError("Supadata job timed out after 2 minutes")

    raise RuntimeError(f"Supadata API error {resp.status_code}: {resp.text[:300]}")


def extract_transcripts(state: AgentState) -> dict:
    """
    For each URL, try transcript extraction in order:

    1. Supadata API  — cloud-IP-safe, no proxy needed (set SUPADATA_API_KEY).
    2. youtube-transcript-api with WebshareProxyConfig  — needs
       WEBSHARE_PROXY_USERNAME + WEBSHARE_PROXY_PASSWORD, or YOUTUBE_PROXY_URL.
    3. yt-dlp + OpenAI Whisper  — audio download fallback; also proxied when set.
       Works for non-YouTube URLs too.
    """
    transcripts: List[Dict] = []
    warnings: List[str] = []
    supadata_key = os.environ.get("SUPADATA_API_KEY")
    ytt_proxy_cfg, ytdlp_proxy_url = _build_proxy_config()

    for url in state["video_urls"]:
        entry: Dict[str, Any] = {
            "url": url,
            "transcript_text": "",
            "source": "none",
            "error": None,
        }
        video_id = _extract_youtube_id(url)

        # ── Method 1: Supadata API (works from any cloud IP) ──────────────────
        if supadata_key:
            try:
                text = _supadata_fetch(url, supadata_key)
                if text.strip():
                    entry["transcript_text"] = text
                    entry["source"] = "supadata"
                    if video_id:
                        entry["video_id"] = video_id
                    transcripts.append(entry)
                    continue
                else:
                    warnings.append(f"Supadata returned empty transcript for {url}")
            except Exception as sup_err:
                warnings.append(f"Supadata failed for {url}: {sup_err}")

        # ── Method 2: youtube-transcript-api with ProxyConfig ─────────────────
        if video_id:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi

                ytt = YouTubeTranscriptApi(proxy_config=ytt_proxy_cfg)

                # Strategy A: direct fetch (default/English)
                fetched = None
                fetch_err = None
                try:
                    fetched = ytt.fetch(video_id)
                except Exception as e:
                    fetch_err = e

                # Strategy B: list → prefer manual EN → auto EN → any
                if fetched is None:
                    list_err = None
                    try:
                        tlist = ytt.list(video_id)
                        for finder in (
                            lambda: tlist.find_manually_created_transcript(["en", "en-US", "en-GB"]),
                            lambda: tlist.find_generated_transcript(["en", "en-US", "en-GB"]),
                            lambda: tlist.find_transcript(["en", "en-US", "en-GB"]),
                            lambda: next(iter(tlist)),
                        ):
                            try:
                                fetched = finder().fetch()
                                break
                            except Exception:
                                continue
                    except Exception as e:
                        list_err = e

                if fetched is None:
                    details = "; ".join(filter(None, [str(fetch_err), str(list_err)]))
                    raise RuntimeError(f"No transcript found ({details})")

                try:
                    text = " ".join(snippet.text for snippet in fetched)
                except AttributeError:
                    text = " ".join(item["text"] for item in fetched)

                entry["transcript_text"] = text
                entry["source"] = "youtube_transcript_api"
                entry["video_id"] = video_id
                transcripts.append(entry)
                continue

            except Exception as yt_err:
                warnings.append(f"YouTube Transcript API failed for {url}: {yt_err}")

        # ── Method 3: yt-dlp + OpenAI Whisper ────────────────────────────────
        # Tries android → ios → web player clients.
        # Uses --proxy when a proxy URL is available.
        proxy_args = ["--proxy", ytdlp_proxy_url] if ytdlp_proxy_url else []
        ytdlp_success = False
        for player_client in ("android", "ios", "web"):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    audio_out = os.path.join(tmpdir, "audio.%(ext)s")
                    result = subprocess.run(
                        [
                            "yt-dlp",
                            "-x",
                            "--audio-format", "mp3",
                            "--audio-quality", "5",
                            "--extractor-args", f"youtube:player_client={player_client}",
                            "--no-check-certificate",
                            *proxy_args,
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
                        raise RuntimeError(
                            f"yt-dlp exit {result.returncode}: {result.stderr[:400]}"
                        )

                    import openai as _openai
                    oai = _openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
                    with open(audio_file, "rb") as f:
                        resp = oai.audio.transcriptions.create(model="whisper-1", file=f)
                    entry["transcript_text"] = resp.text
                    entry["source"] = f"whisper ({player_client} client)"
                    ytdlp_success = True
                    break
            except Exception as dl_err:
                warnings.append(f"yt-dlp ({player_client}) failed for {url}: {dl_err}")

        if not ytdlp_success:
            entry["error"] = "All transcript extraction methods failed — see warnings"

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

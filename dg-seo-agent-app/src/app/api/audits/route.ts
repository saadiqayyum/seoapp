import { NextResponse } from "next/server";
import { requireSession } from "@/lib/auth";
import { createAudit, listAudits } from "@/lib/audits";

export async function GET(request: Request) {
  const session = await requireSession();
  const { searchParams } = new URL(request.url);
  const domainId = searchParams.get("domainId");
  if (!domainId) {
    return NextResponse.json({ error: "domainId is required" }, { status: 400 });
  }
  const rows = await listAudits(session.userId!, domainId);
  return NextResponse.json({ audits: rows });
}

export async function POST(request: Request) {
  const session = await requireSession();

  let body: { domainId?: string; keywords?: string[] };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!body.domainId || !Array.isArray(body.keywords)) {
    return NextResponse.json(
      { error: "domainId and keywords are required" },
      { status: 400 },
    );
  }

  const cleaned = body.keywords
    .map((k) => k.trim())
    .filter((k) => k.length > 0);
  if (cleaned.length === 0) {
    return NextResponse.json(
      { error: "At least one non-empty keyword is required" },
      { status: 400 },
    );
  }

  try {
    const audit = await createAudit(session.userId!, body.domainId, cleaned);
    return NextResponse.json({ audit }, { status: 201 });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Failed to create audit";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

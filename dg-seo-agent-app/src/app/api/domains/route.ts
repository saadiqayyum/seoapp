import { NextResponse } from "next/server";
import { requireSession } from "@/lib/auth";
import { createDomain, listDomains } from "@/lib/domains";

export async function GET() {
  const session = await requireSession();
  const rows = await listDomains(session.userId!);
  return NextResponse.json({ domains: rows });
}

export async function POST(request: Request) {
  const session = await requireSession();

  let body: { url?: string; label?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!body.url) {
    return NextResponse.json({ error: "url is required" }, { status: 400 });
  }

  try {
    const domain = await createDomain(session.userId!, {
      url: body.url,
      label: body.label,
    });
    return NextResponse.json({ domain }, { status: 201 });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Failed to create domain";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

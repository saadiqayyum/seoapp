import { NextResponse } from "next/server";
import { getSession, requireSession } from "@/lib/auth";
import { getDomain } from "@/lib/domains";

export async function POST(request: Request) {
  await requireSession();

  let body: { domainId?: string | null };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const session = await getSession();

  if (body.domainId === null) {
    session.currentDomainId = undefined;
    await session.save();
    return NextResponse.json({ currentDomainId: null });
  }

  if (!body.domainId) {
    return NextResponse.json({ error: "domainId is required" }, { status: 400 });
  }

  // Verify ownership before storing in session
  const domain = await getDomain(session.userId!, body.domainId);
  if (!domain) {
    return NextResponse.json({ error: "Domain not found" }, { status: 404 });
  }

  session.currentDomainId = body.domainId;
  await session.save();

  return NextResponse.json({ currentDomainId: body.domainId });
}

import { NextResponse } from "next/server";
import { requireSession } from "@/lib/auth";
import { getAuditDetail } from "@/lib/audits";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await requireSession();
  const { id } = await params;

  const audit = await getAuditDetail(session.userId!, id);
  if (!audit) {
    return NextResponse.json({ error: "Audit not found" }, { status: 404 });
  }
  return NextResponse.json({ audit });
}

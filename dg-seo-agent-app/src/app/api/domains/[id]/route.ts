import { NextResponse } from "next/server";
import { requireSession } from "@/lib/auth";
import { deleteDomain } from "@/lib/domains";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await requireSession();
  const { id } = await params;

  const ok = await deleteDomain(session.userId!, id);
  if (!ok) {
    return NextResponse.json({ error: "Domain not found" }, { status: 404 });
  }
  return NextResponse.json({ ok: true });
}

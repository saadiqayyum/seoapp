import { NextResponse } from "next/server";
import { getCurrentDomainId, getSession } from "@/lib/auth";

export async function GET() {
  const session = await getSession();
  if (!session.userId) {
    return NextResponse.json(
      { user: null, currentDomainId: null },
      { status: 200 },
    );
  }
  const currentDomainId = await getCurrentDomainId(session);
  return NextResponse.json({
    user: { userId: session.userId, email: session.email },
    currentDomainId,
  });
}

import { NextResponse } from "next/server";
import { ensureAdminSeeded, getSession, verifyCredentials } from "@/lib/auth";

export async function POST(request: Request) {
  await ensureAdminSeeded();

  let body: { email?: string; password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const { email, password } = body;
  if (!email || !password) {
    return NextResponse.json(
      { error: "Email and password are required" },
      { status: 400 },
    );
  }

  const user = await verifyCredentials(email, password);
  if (!user) {
    return NextResponse.json(
      { error: "Invalid email or password" },
      { status: 401 },
    );
  }

  const session = await getSession();
  session.userId = user.userId;
  session.email = user.email;
  await session.save();

  return NextResponse.json({ userId: user.userId, email: user.email });
}

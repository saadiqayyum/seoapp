import { cookies } from "next/headers";
import { getIronSession, SessionOptions } from "iron-session";
import bcrypt from "bcryptjs";
import { users, domains, ObjectId } from "./db";

export interface SessionData {
  userId?: string;            // ObjectId string
  email?: string;
  currentDomainId?: string;   // selected domain, stored in session cookie
}

const password = process.env.SESSION_PASSWORD;
if (!password || password.length < 32) {
  throw new Error("SESSION_PASSWORD must be set and at least 32 chars");
}

const sessionOptions: SessionOptions = {
  password,
  cookieName: "dg_seo_session",
  cookieOptions: {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  },
};

export async function getSession() {
  return getIronSession<SessionData>(await cookies(), sessionOptions);
}

export async function requireSession() {
  const session = await getSession();
  if (!session.userId) {
    throw new AuthError("Not authenticated");
  }
  return session;
}

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthError";
  }
}

// ── Admin seeding ────────────────────────────────────────────────────────

let seedPromise: Promise<void> | null = null;

export function ensureAdminSeeded(): Promise<void> {
  if (!seedPromise) {
    seedPromise = seedAdmin();
  }
  return seedPromise;
}

async function seedAdmin(): Promise<void> {
  const email = process.env.ADMIN_EMAIL;
  const plaintext = process.env.ADMIN_PASSWORD;
  if (!email || !plaintext) {
    throw new Error("ADMIN_EMAIL and ADMIN_PASSWORD must be set");
  }

  const col = await users();
  const existing = await col.findOne({ email });
  if (existing) return;

  const passwordHash = await bcrypt.hash(plaintext, 10);
  await col.insertOne({
    _id: new ObjectId(),
    email,
    passwordHash,
    createdAt: new Date(),
  });
}

export async function verifyCredentials(
  email: string,
  plaintext: string,
): Promise<{ userId: string; email: string } | null> {
  const col = await users();
  const user = await col.findOne({ email });
  if (!user) return null;
  const ok = await bcrypt.compare(plaintext, user.passwordHash);
  if (!ok) return null;
  return { userId: user._id.toString(), email: user.email };
}

// ── Current domain helpers ───────────────────────────────────────────────

export async function getCurrentDomainId(
  session: SessionData,
): Promise<string | null> {
  if (session.currentDomainId) return session.currentDomainId;
  if (!session.userId) return null;

  // Auto-pick the first active domain if none selected
  const col = await domains();
  const first = await col.findOne(
    { userId: new ObjectId(session.userId), isActive: true },
    { sort: { createdAt: 1 } },
  );
  return first ? first._id.toString() : null;
}

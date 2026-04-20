import { MongoClient, Db, Collection, ObjectId } from "mongodb";
import type { ReportData } from "./types";

const uri = process.env.MONGO_URI;
if (!uri) {
  throw new Error("MONGO_URI is not set");
}

// Next.js hot-reload in dev rebuilds modules; cache the client on globalThis
// so we don't leak connections across reloads.
const globalForMongo = globalThis as unknown as {
  _mongoClient?: MongoClient;
  _mongoClientPromise?: Promise<MongoClient>;
};

function getClient(): Promise<MongoClient> {
  if (!globalForMongo._mongoClientPromise) {
    globalForMongo._mongoClient = new MongoClient(uri!);
    globalForMongo._mongoClientPromise = globalForMongo._mongoClient.connect();
  }
  return globalForMongo._mongoClientPromise;
}

export async function getDb(): Promise<Db> {
  const client = await getClient();
  // DB name is embedded in the URI path; MongoClient resolves it from there
  return client.db();
}

// ── Document schemas ─────────────────────────────────────────────────────

export interface UserDoc {
  _id: ObjectId;
  email: string;
  passwordHash: string;
  createdAt: Date;
}

export interface DomainDoc {
  _id: ObjectId;
  userId: ObjectId;
  url: string;          // e.g. "https://example.com"
  label: string;        // display name, defaults to hostname
  isActive: boolean;
  createdAt: Date;
}

export type AuditStatus = "pending" | "running" | "complete" | "failed";

export interface AuditDoc {
  _id: ObjectId;
  userId: ObjectId;
  domainId: ObjectId;
  keywords: string[];
  status: AuditStatus;
  threadId: string | null;
  assistantId: string;
  report: ReportData | null;   // full structured agent output
  error: string | null;
  createdAt: Date;
  startedAt: Date | null;
  completedAt: Date | null;
}

export async function users(): Promise<Collection<UserDoc>> {
  return (await getDb()).collection<UserDoc>("users");
}

export async function domains(): Promise<Collection<DomainDoc>> {
  const col = (await getDb()).collection<DomainDoc>("domains");
  await col.createIndex({ userId: 1, isActive: 1 }).catch(() => {});
  return col;
}

export async function audits(): Promise<Collection<AuditDoc>> {
  const col = (await getDb()).collection<AuditDoc>("audits");
  await col.createIndex({ domainId: 1, createdAt: -1 }).catch(() => {});
  await col.createIndex({ userId: 1, createdAt: -1 }).catch(() => {});
  return col;
}

export { ObjectId };

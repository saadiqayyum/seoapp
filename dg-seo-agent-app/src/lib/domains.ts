import { domains, DomainDoc, ObjectId } from "./db";

export interface DomainSummary {
  id: string;
  url: string;
  label: string;
  isActive: boolean;
  createdAt: string;
}

function serialize(doc: DomainDoc): DomainSummary {
  return {
    id: doc._id.toString(),
    url: doc.url,
    label: doc.label,
    isActive: doc.isActive,
    createdAt: doc.createdAt.toISOString(),
  };
}

export async function listDomains(userId: string): Promise<DomainSummary[]> {
  const col = await domains();
  const docs = await col
    .find({ userId: new ObjectId(userId) })
    .sort({ createdAt: 1 })
    .toArray();
  return docs.map(serialize);
}

export async function getDomain(
  userId: string,
  domainId: string,
): Promise<DomainSummary | null> {
  if (!ObjectId.isValid(domainId)) return null;
  const col = await domains();
  const doc = await col.findOne({
    _id: new ObjectId(domainId),
    userId: new ObjectId(userId),
  });
  return doc ? serialize(doc) : null;
}

export async function createDomain(
  userId: string,
  input: { url: string; label?: string },
): Promise<DomainSummary> {
  const url = normalizeUrl(input.url);
  const label = input.label?.trim() || extractHostname(url);

  const col = await domains();
  const doc: DomainDoc = {
    _id: new ObjectId(),
    userId: new ObjectId(userId),
    url,
    label,
    isActive: true,
    createdAt: new Date(),
  };
  await col.insertOne(doc);
  return serialize(doc);
}

export async function deleteDomain(
  userId: string,
  domainId: string,
): Promise<boolean> {
  if (!ObjectId.isValid(domainId)) return false;
  const col = await domains();
  const result = await col.deleteOne({
    _id: new ObjectId(domainId),
    userId: new ObjectId(userId),
  });
  return result.deletedCount === 1;
}

function normalizeUrl(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) throw new Error("URL is required");
  try {
    const u = new URL(trimmed.startsWith("http") ? trimmed : `https://${trimmed}`);
    return u.origin;
  } catch {
    throw new Error("Invalid URL");
  }
}

function extractHostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

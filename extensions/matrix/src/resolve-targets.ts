import type {
  ChannelDirectoryEntry,
  ChannelResolveKind,
  ChannelResolveResult,
  RuntimeEnv,
} from "openclaw/plugin-sdk";
import { listMatrixDirectoryGroupsLive, listMatrixDirectoryPeersLive } from "./directory-live.js";

function pickBestGroupMatch(
  matches: ChannelDirectoryEntry[],
  query: string,
): ChannelDirectoryEntry | undefined {
  if (matches.length === 0) {
    return undefined;
  }
  const normalized = query.trim().toLowerCase();
  if (normalized) {
    const exact = matches.find((match) => {
      const name = match.name?.trim().toLowerCase();
      const handle = match.handle?.trim().toLowerCase();
      const id = match.id.trim().toLowerCase();
      return name === normalized || handle === normalized || id === normalized;
    });
    if (exact) {
      return exact;
    }
  }
  return matches[0];
}

function pickBestUserMatch(
  matches: ChannelDirectoryEntry[],
  query: string,
): ChannelDirectoryEntry | undefined {
  if (matches.length === 0) {
    return undefined;
  }
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return undefined;
  }
  const exact = matches.filter((match) => {
    const id = match.id.trim().toLowerCase();
    const name = match.name?.trim().toLowerCase();
    const handle = match.handle?.trim().toLowerCase();
    return normalized === id || normalized === name || normalized === handle;
  });
  if (exact.length === 1) {
    return exact[0];
  }
  return undefined;
}

function describeUserMatchFailure(matches: ChannelDirectoryEntry[], query: string): string {
  if (matches.length === 0) {
    return "no matches";
  }
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return "empty input";
  }
  const exact = matches.filter((match) => {
    const id = match.id.trim().toLowerCase();
    const name = match.name?.trim().toLowerCase();
    const handle = match.handle?.trim().toLowerCase();
    return normalized === id || normalized === name || normalized === handle;
  });
  if (exact.length === 0) {
    return "no exact match; use full Matrix ID";
  }
  if (exact.length > 1) {
    return "multiple exact matches; use full Matrix ID";
  }
  return "no exact match; use full Matrix ID";
}

export async function resolveMatrixTargets(params: {
  cfg: unknown;
  inputs: string[];
  kind: ChannelResolveKind;
  runtime?: RuntimeEnv;
}): Promise<ChannelResolveResult[]> {
  const promises = params.inputs.map(async (input) => {
    const trimmed = input.trim();
    if (!trimmed) {
      return { input, resolved: false, note: "empty input" } satisfies ChannelResolveResult;
    }
    if (params.kind === "user") {
      if (trimmed.startsWith("@") && trimmed.includes(":")) {
        return { input, resolved: true, id: trimmed } satisfies ChannelResolveResult;
      }
      try {
        const matches = await listMatrixDirectoryPeersLive({
          cfg: params.cfg,
          query: trimmed,
          limit: 5,
        });
        const best = pickBestUserMatch(matches, trimmed);
        return {
          input,
          resolved: Boolean(best?.id),
          id: best?.id,
          name: best?.name,
          note: best ? undefined : describeUserMatchFailure(matches, trimmed),
        } satisfies ChannelResolveResult;
      } catch (err) {
        params.runtime?.error?.(`matrix resolve failed: ${String(err)}`);
        return { input, resolved: false, note: "lookup failed" } satisfies ChannelResolveResult;
      }
    }
    try {
      const matches = await listMatrixDirectoryGroupsLive({
        cfg: params.cfg,
        query: trimmed,
        limit: 5,
      });
      const best = pickBestGroupMatch(matches, trimmed);
      return {
        input,
        resolved: Boolean(best?.id),
        id: best?.id,
        name: best?.name,
        note: matches.length > 1 ? "multiple matches; chose first" : undefined,
      } satisfies ChannelResolveResult;
    } catch (err) {
      params.runtime?.error?.(`matrix resolve failed: ${String(err)}`);
      return { input, resolved: false, note: "lookup failed" } satisfies ChannelResolveResult;
    }
  });
  return Promise.all(promises);
}


import { performance } from "perf_hooks";
import { findFirstMatch } from "../../src/utils/array.js";

const MAX_ASSISTANT_NAME = 50;
const MAX_ASSISTANT_AVATAR = 200;
const MAX_ASSISTANT_EMOJI = 16;

export const DEFAULT_ASSISTANT_IDENTITY = {
  agentId: "main",
  name: "Assistant",
  avatar: "A",
};

function coerceIdentityValue(value: string | undefined, maxLength: number): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  if (trimmed.length <= maxLength) {
    return trimmed;
  }
  return trimmed.slice(0, maxLength);
}

function isAvatarUrl(value: string): boolean {
  return /^https?:\/\//i.test(value) || /^data:image\//i.test(value);
}

function looksLikeAvatarPath(value: string): boolean {
  if (/[\\/]/.test(value)) {
    return true;
  }
  return /\.(png|jpe?g|gif|webp|svg|ico)$/i.test(value);
}

function normalizeAvatarValue(value: string | undefined): string | undefined {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  if (isAvatarUrl(trimmed)) {
    return trimmed;
  }
  if (looksLikeAvatarPath(trimmed)) {
    return trimmed;
  }
  if (!/\s/.test(trimmed) && trimmed.length <= 4) {
    return trimmed;
  }
  return undefined;
}

// Current Implementation
function resolveAvatarCurrent(candidates: (string | undefined)[]): string {
    return candidates.map((candidate) => normalizeAvatarValue(candidate)).find(Boolean) ??
    DEFAULT_ASSISTANT_IDENTITY.avatar;
}

// Optimized Implementation using findFirstMatch
function resolveAvatarOptimized(candidates: (string | undefined)[]): string {
    return findFirstMatch(candidates, normalizeAvatarValue) ?? DEFAULT_ASSISTANT_IDENTITY.avatar;
}

const iterations = 1_000_000;
const testCases = [
    [undefined, undefined, undefined, undefined, undefined],
    ["valid.png", undefined, undefined, undefined, undefined],
    [undefined, undefined, "valid.png", undefined, undefined],
    [undefined, undefined, undefined, undefined, "valid.png"],
    ["invalid", "also invalid", "valid.png", "ignored", "ignored"],
    ["  ", undefined, "  valid.png  ", undefined, undefined]
];

console.log(`Running benchmark with ${iterations} iterations per test case...`);

let start = performance.now();
for (let i = 0; i < iterations; i++) {
    for (const testCase of testCases) {
        resolveAvatarCurrent(testCase);
    }
}
let end = performance.now();
console.log(`Current Implementation: ${(end - start).toFixed(2)}ms`);

start = performance.now();
for (let i = 0; i < iterations; i++) {
    for (const testCase of testCases) {
        resolveAvatarOptimized(testCase);
    }
}
end = performance.now();
console.log(`Optimized Implementation (findFirstMatch): ${(end - start).toFixed(2)}ms`);

import { describe, expect, it, vi, beforeEach } from "vitest";
import { FailoverError } from "../failover-error.js";
import { isFailoverErrorMessage, classifyFailoverReason } from "../pi-embedded-helpers.js";

vi.mock("./run/attempt.js", () => ({
  runEmbeddedAttempt: vi.fn(),
}));

vi.mock("./compact.js", () => ({
  compactEmbeddedPiSessionDirect: vi.fn(),
}));

vi.mock("./model.js", () => ({
  resolveModel: vi.fn(() => ({
    model: {
      id: "test-model",
      provider: "anthropic",
      contextWindow: 200000,
      api: "messages",
    },
    error: null,
    authStorage: {
      setRuntimeApiKey: vi.fn(),
    },
    modelRegistry: {},
  })),
}));

vi.mock("../model-auth.js", () => ({
  ensureAuthProfileStore: vi.fn(() => ({})),
  getApiKeyForModel: vi.fn(async () => ({
    apiKey: "test-key",
    profileId: "test-profile",
    source: "test",
  })),
  resolveAuthProfileOrder: vi.fn(() => []),
}));

vi.mock("../models-config.js", () => ({
  ensureOpenClawModelsJson: vi.fn(async () => {}),
}));

vi.mock("../context-window-guard.js", () => ({
  CONTEXT_WINDOW_HARD_MIN_TOKENS: 1000,
  CONTEXT_WINDOW_WARN_BELOW_TOKENS: 5000,
  evaluateContextWindowGuard: vi.fn(() => ({
    shouldWarn: false,
    shouldBlock: false,
    tokens: 200000,
    source: "model",
  })),
  resolveContextWindowInfo: vi.fn(() => ({
    tokens: 200000,
    source: "model",
  })),
}));

vi.mock("../../process/command-queue.js", () => ({
  enqueueCommandInLane: vi.fn((_lane: string, task: () => unknown) => task()),
}));

vi.mock("../../utils.js", () => ({
  resolveUserPath: vi.fn((p: string) => p),
}));

vi.mock("../../utils/message-channel.js", () => ({
  isMarkdownCapableMessageChannel: vi.fn(() => true),
}));

vi.mock("../agent-paths.js", () => ({
  resolveOpenClawAgentDir: vi.fn(() => "/tmp/agent-dir"),
}));

vi.mock("../auth-profiles.js", () => ({
  markAuthProfileFailure: vi.fn(async () => {}),
  markAuthProfileGood: vi.fn(async () => {}),
  markAuthProfileUsed: vi.fn(async () => {}),
}));

vi.mock("../defaults.js", () => ({
  DEFAULT_CONTEXT_TOKENS: 200000,
  DEFAULT_MODEL: "test-model",
  DEFAULT_PROVIDER: "anthropic",
}));

vi.mock("../failover-error.js", () => ({
  FailoverError: class extends Error {
    reason: string;
    provider: string;
    model: string;
    profileId: string;
    status: number;
    constructor(message: string, params: any) {
      super(message);
      this.name = "FailoverError";
      this.reason = params.reason;
      this.provider = params.provider;
      this.model = params.model;
      this.profileId = params.profileId;
      this.status = params.status;
    }
  },
  resolveFailoverStatus: vi.fn((reason) => {
      if (reason === "rate_limit") return 429;
      return 500;
  }),
}));

vi.mock("../usage.js", () => ({
  normalizeUsage: vi.fn(() => undefined),
}));

vi.mock("./lanes.js", () => ({
  resolveSessionLane: vi.fn(() => "session-lane"),
  resolveGlobalLane: vi.fn(() => "global-lane"),
}));

vi.mock("./logger.js", () => ({
  log: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("./run/payloads.js", () => ({
  buildEmbeddedRunPayloads: vi.fn(() => []),
}));

vi.mock("./utils.js", () => ({
  describeUnknownError: vi.fn((err: unknown) => {
    if (err instanceof Error) {
      return err.message;
    }
    return String(err);
  }),
}));

vi.mock("../pi-embedded-helpers.js", async () => {
  return {
    isCompactionFailureError: vi.fn(() => false),
    isContextOverflowError: vi.fn(() => false),
    isFailoverAssistantError: vi.fn(() => false),
    isFailoverErrorMessage: vi.fn((msg) => msg?.includes("rate limit")),
    isAuthAssistantError: vi.fn(() => false),
    isRateLimitAssistantError: vi.fn(() => false),
    isBillingAssistantError: vi.fn(() => false),
    classifyFailoverReason: vi.fn((msg) => msg?.includes("rate limit") ? "rate_limit" : null),
    formatAssistantErrorText: vi.fn(() => ""),
    pickFallbackThinkingLevel: vi.fn(() => null),
    isTimeoutErrorMessage: vi.fn(() => false),
    parseImageDimensionError: vi.fn(() => null),
    parseImageSizeError: vi.fn(() => null),
  };
});

import type { EmbeddedRunAttemptResult } from "./run/types.js";
import { runEmbeddedPiAgent } from "./run.js";
import { runEmbeddedAttempt } from "./run/attempt.js";

const mockedRunEmbeddedAttempt = vi.mocked(runEmbeddedAttempt);

function makeAttemptResult(
  overrides: Partial<EmbeddedRunAttemptResult> = {},
): EmbeddedRunAttemptResult {
  return {
    aborted: false,
    timedOut: false,
    promptError: null,
    sessionIdUsed: "test-session",
    assistantTexts: ["Hello!"],
    toolMetas: [],
    lastAssistant: undefined,
    messagesSnapshot: [],
    didSendViaMessagingTool: false,
    messagingToolSentTexts: [],
    messagingToolSentTargets: [],
    cloudCodeAssistFormatError: false,
    ...overrides,
  };
}

const baseParams = {
  sessionId: "test-session",
  sessionKey: "test-key",
  sessionFile: "/tmp/session.json",
  workspaceDir: "/tmp/workspace",
  prompt: "hello",
  timeoutMs: 30000,
  runId: "run-1",
  config: {
    agents: {
      defaults: {
        model: {
          fallbacks: ["fallback-model"]
        }
      }
    }
  }
};

describe("FailoverError handling for prompt errors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("throws FailoverError when fallbackConfigured is true and promptError is a failover error", async () => {
    const rateLimitError = new Error("rate limit exceeded");
    mockedRunEmbeddedAttempt.mockResolvedValue(makeAttemptResult({ promptError: rateLimitError }));

    await expect(runEmbeddedPiAgent(baseParams)).rejects.toThrow("rate limit exceeded");

    // Check if it was a FailoverError (can't use instanceof easily with mocks but we can check properties if we caught it)
    try {
        await runEmbeddedPiAgent(baseParams);
        throw new Error("Should have thrown");
    } catch (err: any) {
        expect(err.name).toBe("FailoverError");
        expect(err.reason).toBe("rate_limit");
        expect(err.status).toBe(429);
        expect(err.provider).toBe("anthropic");
        expect(err.model).toBe("test-model");
    }
  });

  it("does NOT throw FailoverError if fallbacks are NOT configured", async () => {
    const rateLimitError = new Error("rate limit exceeded");
    mockedRunEmbeddedAttempt.mockResolvedValue(makeAttemptResult({ promptError: rateLimitError }));

    const paramsNoFallback = {
        ...baseParams,
        config: {
            agents: {
                defaults: {
                    model: {
                        fallbacks: []
                    }
                }
            }
        }
    };

    await expect(runEmbeddedPiAgent(paramsNoFallback)).rejects.toThrow("rate limit exceeded");

    try {
        await runEmbeddedPiAgent(paramsNoFallback);
        throw new Error("Should have thrown");
    } catch (err: any) {
        expect(err.name).not.toBe("FailoverError");
    }
  });
});

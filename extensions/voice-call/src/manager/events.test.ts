
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { processEvent } from "./events.js";
import type { CallManagerContext } from "./context.js";
import type { VoiceCallProvider } from "../providers/base.js";
import type { HangupCallInput, InitiateCallInput, PlayTtsInput, StartListeningInput, StopListeningInput, WebhookContext, WebhookVerificationResult, ProviderWebhookParseResult, InitiateCallResult } from "../types.js";
import type { VoiceCallConfig } from "../config.js";

class MockProvider implements VoiceCallProvider {
  readonly name = "mock" as const;
  readonly hangupCalls: HangupCallInput[] = [];

  async hangupCall(input: HangupCallInput): Promise<void> {
    this.hangupCalls.push(input);
  }

  // Other methods are not used in this test but required by interface
  verifyWebhook(_ctx: WebhookContext): WebhookVerificationResult { return { ok: true }; }
  parseWebhookEvent(_ctx: WebhookContext): ProviderWebhookParseResult { return { events: [], statusCode: 200 }; }
  async initiateCall(_input: InitiateCallInput): Promise<InitiateCallResult> { return { providerCallId: "mock-id", status: "initiated" }; }
  async playTts(_input: PlayTtsInput): Promise<void> {}
  async startListening(_input: StartListeningInput): Promise<void> {}
  async stopListening(_input: StopListeningInput): Promise<void> {}
}

describe("processEvent", () => {
  it("should hang up inbound calls that are rejected by policy", () => {
    const provider = new MockProvider();
    const config: VoiceCallConfig = {
      enabled: true,
      provider: "mock",
      inboundPolicy: "allowlist",
      allowFrom: ["+15550001234"], // Only allow this number
    };

    const storePath = fs.mkdtempSync(path.join(os.tmpdir(), "voice-call-test-"));
    const ctx: CallManagerContext = {
      activeCalls: new Map(),
      providerCallIdMap: new Map(),
      processedEventIds: new Set(),
      provider,
      config,
      storePath,
      webhookUrl: "http://localhost:3000/webhook",
      transcriptWaiters: new Map(),
      maxDurationTimers: new Map(),
    };

    // Simulate an inbound call from a disallowed number
    processEvent(ctx, {
      id: "evt-rejected",
      type: "call.initiated",
      callId: "call-rejected",
      providerCallId: "provider-rejected",
      timestamp: Date.now(),
      direction: "inbound",
      from: "+15559999999", // Not in allowlist
      to: "+15550000000",
    });

    // Expect hangup to be called
    expect(provider.hangupCalls).toHaveLength(1);
    expect(provider.hangupCalls[0]?.providerCallId).toBe("provider-rejected");
    expect(provider.hangupCalls[0]?.reason).toBe("hangup-bot");
  });

  it("should not hang up inbound calls that are accepted by policy", () => {
    const provider = new MockProvider();
    const config: VoiceCallConfig = {
      enabled: true,
      provider: "mock",
      inboundPolicy: "allowlist",
      allowFrom: ["+15550001234"],
    };

    const storePath = fs.mkdtempSync(path.join(os.tmpdir(), "voice-call-test-"));
    const ctx: CallManagerContext = {
      activeCalls: new Map(),
      providerCallIdMap: new Map(),
      processedEventIds: new Set(),
      provider,
      config,
      storePath,
      webhookUrl: "http://localhost:3000/webhook",
      transcriptWaiters: new Map(),
      maxDurationTimers: new Map(),
    };

    // Simulate an inbound call from an allowed number
    processEvent(ctx, {
      id: "evt-accepted",
      type: "call.initiated",
      callId: "call-accepted",
      providerCallId: "provider-accepted",
      timestamp: Date.now(),
      direction: "inbound",
      from: "+15550001234", // In allowlist
      to: "+15550000000",
    });

    // Expect hangup NOT to be called
    expect(provider.hangupCalls).toHaveLength(0);

    // Expect call to be created
    expect(ctx.activeCalls.size).toBe(1);
  });
});

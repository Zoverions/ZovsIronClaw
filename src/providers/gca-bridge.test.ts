import { describe, expect, it } from "vitest";
import { GCABridgeProvider } from "./gca-bridge.js";

describe("GCABridgeProvider", () => {
  it("generates unique tool call IDs in the correct format", () => {
    const provider = new GCABridgeProvider();
    // Accessing private method for testing purposes
    const toolCallId = (provider as any).generateToolCallId();

    // Format: gca_<timestamp>_<hex_random>
    expect(toolCallId).toMatch(/^gca_\d+_[a-f0-9]{10}$/);
  });

  it("generates different IDs on consecutive calls", () => {
    const provider = new GCABridgeProvider();
    const id1 = (provider as any).generateToolCallId();
    const id2 = (provider as any).generateToolCallId();

    expect(id1).not.toBe(id2);
  });
});

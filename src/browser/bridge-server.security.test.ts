import { describe, it, expect, afterEach } from "vitest";
import { startBrowserBridgeServer, stopBrowserBridgeServer, type BrowserBridge } from "./bridge-server.js";
import type { ResolvedBrowserConfig } from "./config.js";

describe("BrowserBridge Server Security", () => {
  let bridge: BrowserBridge | null = null;

  afterEach(async () => {
    if (bridge) {
      await stopBrowserBridgeServer(bridge.server);
      bridge = null;
    }
  });

  const mockConfig: ResolvedBrowserConfig = {
    enabled: true,
    controlPort: 0,
    profiles: {},
  };

  it("should have CORS headers", async () => {
    bridge = await startBrowserBridgeServer({
      resolved: mockConfig,
      host: "127.0.0.1",
      port: 0,
    });

    const res = await fetch(`${bridge.baseUrl}/health`, { method: "OPTIONS" });
    expect(res.headers.get("Access-Control-Allow-Origin")).toBe("*");
    expect(res.headers.get("Access-Control-Allow-Methods")).toContain("GET");
    expect(res.status).toBe(204);
  });

  it("should rate limit requests", async () => {
    bridge = await startBrowserBridgeServer({
      resolved: mockConfig,
      host: "127.0.0.1",
      port: 0,
    });

    const res = await fetch(`${bridge.baseUrl}/health`);
    expect(res.status).not.toBe(429);
  });
});

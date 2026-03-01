import crypto from "node:crypto";
import sharp from "sharp";
import { describe, expect, it, vi } from "vitest";
import * as imageOps from "../media/image-ops.js";
import { normalizeBrowserScreenshot } from "./screenshot.js";

describe("browser screenshot performance", () => {
  it("measures resize calls for hard-to-compress images", async () => {
    // Generate a high-entropy image (random noise) that is hard to compress
    const width = 2500;
    const height = 2500;
    const raw = crypto.randomBytes(width * height * 3);
    const bigPng = await sharp(raw, { raw: { width, height, channels: 3 } })
      .png({ compressionLevel: 0 })
      .toBuffer();

    // Spy on resizeToJpeg to count calls
    const resizeSpy = vi.spyOn(imageOps, "resizeToJpeg");

    try {
      // Set a very low maxBytes to force multiple resize attempts
      // 500KB is very small for a 2500x2500 noise image, likely forcing it down the grid
      await normalizeBrowserScreenshot(bigPng, {
        maxSide: 2000,
        maxBytes: 500 * 1024,
      }).catch(() => {
        // It might fail completely if it can't reach the target size, which is fine for counting calls
      });

      const callCount = resizeSpy.mock.calls.length;
      console.log(`[Perf] Hard image resize calls: ${callCount}`);

      // We expect a high number of calls in the unoptimized version
      // because it tries every quality level for every side dimension until it fails or succeeds.
      // If 2000px fails at Q35, it will have tried 85, 75, 65, 55, 45, 35 (6 calls).
      // Then it moves to 1800px, etc.
      expect(callCount).toBeGreaterThan(0);

    } finally {
      resizeSpy.mockRestore();
    }
  }, 120_000);

  it("measures resize calls for easy-to-compress images", async () => {
    // Solid color image
    const width = 2500;
    const height = 2500;
    const solid = await sharp({
      create: {
        width,
        height,
        channels: 3,
        background: { r: 255, g: 0, b: 0 },
      },
    })
      .png()
      .toBuffer();

    const resizeSpy = vi.spyOn(imageOps, "resizeToJpeg");

    try {
      await normalizeBrowserScreenshot(solid, {
        maxSide: 2000,
        maxBytes: 5 * 1024 * 1024,
      });

      const callCount = resizeSpy.mock.calls.length;
      console.log(`[Perf] Easy image resize calls: ${callCount}`);

      // Should succeed on the first try (2000px, Q85)
      expect(callCount).toBe(1);
    } finally {
      resizeSpy.mockRestore();
    }
  });
});

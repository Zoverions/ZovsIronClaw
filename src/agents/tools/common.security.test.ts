import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import path from "node:path";
import fs from "node:fs/promises";
import os from "node:os";

// Mock resolveConfigDir before importing common.js
const testConfigDir = path.join(os.tmpdir(), "openclaw-test-" + Date.now());

vi.mock("../../utils.js", async (importOriginal) => {
  // eslint-disable-next-line @typescript-eslint/consistent-type-imports
  const actual = await importOriginal<typeof import("../../utils.js")>();
  return {
    ...actual,
    resolveConfigDir: () => testConfigDir,
  };
});

// Import after mock
import { imageResultFromFile } from "./common.js";

describe("imageResultFromFile security check", () => {
  const mediaDir = path.join(testConfigDir, "media");

  beforeAll(async () => {
    await fs.mkdir(mediaDir, { recursive: true });
  });

  afterAll(async () => {
    await fs.rm(testConfigDir, { recursive: true, force: true });
  });

  it("should fail to read arbitrary file outside allowed media directory", async () => {
    const targetPath = path.resolve("package.json");
    await expect(imageResultFromFile({
      label: "exploit",
      path: targetPath
    })).rejects.toThrow("Access denied");
  });

  it("should allow reading file inside allowed media directory", async () => {
    const filePath = path.join(mediaDir, "test.png");
    // Create a dummy file (valid png header)
    const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
    await fs.writeFile(filePath, pngSignature);

    await expect(imageResultFromFile({
      label: "valid",
      path: filePath
    })).resolves.not.toThrow();
  });

  it("should fail to read file with path traversal attempting to escape media directory", async () => {
    // create a file outside
    const outsideFile = path.join(testConfigDir, "outside.txt");
    await fs.writeFile(outsideFile, "secret");

    // try to access it via traversal from media dir
    const traversalPath = path.join(mediaDir, "..", "outside.txt");

    await expect(imageResultFromFile({
      label: "traversal",
      path: traversalPath
    })).rejects.toThrow("Access denied");
  });

  it("should fail to read file with partial path match", async () => {
    // create a file named 'media_hack' in the config dir
    const hackFile = path.join(testConfigDir, "media_hack");
    await fs.writeFile(hackFile, "hack");

    // The media dir is '.../media'. '.../media_hack' starts with '.../media' string-wise but is outside.

    await expect(imageResultFromFile({
      label: "partial",
      path: hackFile
    })).rejects.toThrow("Access denied");
  });
});

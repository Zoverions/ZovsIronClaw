import { describe, expect, it, vi } from "vitest";
import { runExec, runCommandWithTimeout } from "./exec.js";
import { execFile, spawn } from "node:child_process";

vi.mock("node:child_process", async () => {
  const actual = await vi.importActual("node:child_process");
  return {
    ...actual,
    execFile: vi.fn(),
    spawn: vi.fn(),
  };
});

describe("exec security", () => {
  describe("runExec", () => {
    it("sanitizes null bytes in arguments", async () => {
      const mockExecFile = vi.mocked(execFile);
      // @ts-ignore
      mockExecFile.mockImplementation((cmd, args, opts, callback) => {
        callback(null, { stdout: "ok", stderr: "" });
      });

      await runExec("ls", ["file\0.txt", "another\x1Ffile"]);

      expect(mockExecFile).toHaveBeenCalledWith(
        expect.any(String),
        ["file.txt", "anotherfile"],
        expect.any(Object)
      );
    });

    it("sanitizes null bytes in command", async () => {
      const mockExecFile = vi.mocked(execFile);
      // @ts-ignore
      mockExecFile.mockImplementation((cmd, args, opts, callback) => {
        callback(null, { stdout: "ok", stderr: "" });
      });

      await runExec("ls\0", ["-la"]);

      expect(mockExecFile).toHaveBeenCalledWith(
        "ls",
        ["-la"],
        expect.any(Object)
      );
    });
  });

  describe("runCommandWithTimeout", () => {
    it("sanitizes null bytes in argv", async () => {
      const mockSpawn = vi.mocked(spawn);
      // @ts-ignore
      mockSpawn.mockReturnValue({
        on: vi.fn(),
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        kill: vi.fn(),
      });

      // runCommandWithTimeout doesn't return until 'close' is emitted,
      // but we just want to check the spawn call.
      runCommandWithTimeout(["echo\0", "hello\x00world"], 5000).catch(() => {});

      expect(mockSpawn).toHaveBeenCalledWith(
        "echo",
        ["helloworld"],
        expect.any(Object)
      );
    });
  });
});

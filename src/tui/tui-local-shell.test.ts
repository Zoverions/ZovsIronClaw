import { describe, expect, it, vi } from "vitest";
import { createLocalShellRunner } from "./tui-local-shell.js";

const createSelector = () => {
  const selector = {
    onSelect: undefined as ((item: { value: string; label: string }) => void) | undefined,
    onCancel: undefined as (() => void) | undefined,
    render: () => ["selector"],
    invalidate: () => {},
  };
  return selector;
};

describe("createLocalShellRunner", () => {
  it("logs denial on subsequent ! attempts without re-prompting", async () => {
    const messages: string[] = [];
    const chatLog = {
      addSystem: (line: string) => {
        messages.push(line);
      },
    };
    const tui = { requestRender: vi.fn() };
    const openOverlay = vi.fn();
    const closeOverlay = vi.fn();
    let lastSelector: ReturnType<typeof createSelector> | null = null;
    const createSelectorSpy = vi.fn(() => {
      lastSelector = createSelector();
      return lastSelector;
    });
    const spawnCommand = vi.fn();

    const { runLocalShellLine } = createLocalShellRunner({
      chatLog,
      tui,
      openOverlay,
      closeOverlay,
      createSelector: createSelectorSpy,
      spawnCommand,
    });

    const firstRun = runLocalShellLine("!ls");
    expect(openOverlay).toHaveBeenCalledTimes(1);
    lastSelector?.onSelect?.({ value: "no", label: "No" });
    await firstRun;

    await runLocalShellLine("!pwd");

    expect(messages).toContain("local shell: not enabled");
    expect(messages).toContain("local shell: not enabled for this session");
    expect(createSelectorSpy).toHaveBeenCalledTimes(1);
    expect(spawnCommand).not.toHaveBeenCalled();
  });

  it("fails to parse malformed command", async () => {
    const messages: string[] = [];
    const chatLog = {
      addSystem: (line: string) => {
        messages.push(line);
      },
    };
    const tui = { requestRender: vi.fn() };
    const openOverlay = vi.fn();
    const closeOverlay = vi.fn();
    let lastSelector: ReturnType<typeof createSelector> | null = null;
    const createSelectorSpy = vi.fn(() => {
      lastSelector = createSelector();
      return lastSelector;
    });
    const spawnCommand = vi.fn();

    const { runLocalShellLine } = createLocalShellRunner({
      chatLog,
      tui,
      openOverlay,
      closeOverlay,
      createSelector: createSelectorSpy,
      spawnCommand,
    });

    const firstRun = runLocalShellLine("!echo 'unclosed");
    expect(openOverlay).toHaveBeenCalledTimes(1);
    lastSelector?.onSelect?.({ value: "yes", label: "Yes" });
    await firstRun;

    expect(messages).toContain("local shell: failed to parse command");
    expect(spawnCommand).not.toHaveBeenCalled();
  });

  it("calls spawnCommand with split arguments and without shell: true", async () => {
    const messages: string[] = [];
    const chatLog = {
      addSystem: (line: string) => {
        messages.push(line);
      },
    };
    const tui = { requestRender: vi.fn() };
    const openOverlay = vi.fn();
    const closeOverlay = vi.fn();
    let lastSelector: ReturnType<typeof createSelector> | null = null;
    const createSelectorSpy = vi.fn(() => {
      lastSelector = createSelector();
      return lastSelector;
    });

    const mockChildProcess = {
      stdout: { on: vi.fn() },
      stderr: { on: vi.fn() },
      on: vi.fn((event, callback) => {
        if (event === "close") {
          setTimeout(() => callback(0, null), 0);
        }
      }),
    };
    const spawnCommand = vi.fn(() => mockChildProcess as unknown as ReturnType<typeof import("node:child_process").spawn>);

    const { runLocalShellLine } = createLocalShellRunner({
      chatLog,
      tui,
      openOverlay,
      closeOverlay,
      createSelector: createSelectorSpy,
      spawnCommand,
      getCwd: () => "/fake/cwd",
      env: { MOCK_ENV: "1" },
    });

    const firstRun = runLocalShellLine("!echo hello world");
    expect(openOverlay).toHaveBeenCalledTimes(1);
    lastSelector?.onSelect?.({ value: "yes", label: "Yes" });
    await firstRun;

    expect(spawnCommand).toHaveBeenCalledTimes(1);
    expect(spawnCommand).toHaveBeenCalledWith("echo", ["hello", "world"], {
      cwd: "/fake/cwd",
      env: { MOCK_ENV: "1" },
    });
  });
});

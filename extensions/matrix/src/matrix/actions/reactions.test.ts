import { describe, expect, it, vi, beforeEach } from "vitest";
import { removeMatrixReactions } from "./reactions.js";
import { resolveActionClient } from "./client.js";
import { resolveMatrixRoomId } from "../send.js";

vi.mock("./client.js", () => ({
  resolveActionClient: vi.fn(),
}));

vi.mock("../send.js", () => ({
  resolveMatrixRoomId: vi.fn(),
}));

describe("removeMatrixReactions", () => {
  const roomId = "!room:example.org";
  const messageId = "$event1";
  const userId = "@user:example.org";

  const mockClient = {
    doRequest: vi.fn(),
    getUserId: vi.fn(),
    redactEvent: vi.fn(),
    stop: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(resolveActionClient).mockResolvedValue({
      client: mockClient,
      stopOnDone: false,
    });
    vi.mocked(resolveMatrixRoomId).mockResolvedValue(roomId);
    mockClient.getUserId.mockResolvedValue(userId);
  });

  it("redacts reactions from the current user", async () => {
    mockClient.doRequest.mockResolvedValue({
      chunk: [
        { event_id: "$reac1", sender: userId, content: { "m.relates_to": { key: "👍" } } },
        { event_id: "$reac2", sender: userId, content: { "m.relates_to": { key: "❤️" } } },
        { event_id: "$reac3", sender: "@other:example.org", content: { "m.relates_to": { key: "👍" } } },
      ],
    });

    const result = await removeMatrixReactions(roomId, messageId);

    expect(result.removed).toBe(2);
    expect(mockClient.redactEvent).toHaveBeenCalledTimes(2);
    expect(mockClient.redactEvent).toHaveBeenCalledWith(roomId, "$reac1");
    expect(mockClient.redactEvent).toHaveBeenCalledWith(roomId, "$reac2");
  });

  it("redacts only specific emoji if provided", async () => {
    mockClient.doRequest.mockResolvedValue({
      chunk: [
        { event_id: "$reac1", sender: userId, content: { "m.relates_to": { key: "👍" } } },
        { event_id: "$reac2", sender: userId, content: { "m.relates_to": { key: "❤️" } } },
      ],
    });

    const result = await removeMatrixReactions(roomId, messageId, { emoji: "👍" });

    expect(result.removed).toBe(1);
    expect(mockClient.redactEvent).toHaveBeenCalledTimes(1);
    expect(mockClient.redactEvent).toHaveBeenCalledWith(roomId, "$reac1");
  });

  it("handles no reactions to remove", async () => {
    mockClient.doRequest.mockResolvedValue({ chunk: [] });

    const result = await removeMatrixReactions(roomId, messageId);

    expect(result.removed).toBe(0);
    expect(mockClient.redactEvent).not.toHaveBeenCalled();
  });

  it("can handle a large number of reactions (to be optimized)", async () => {
    const manyReactions = Array.from({ length: 25 }, (_, i) => ({
      event_id: `$reac${i}`,
      sender: userId,
      content: { "m.relates_to": { key: "👍" } },
    }));
    mockClient.doRequest.mockResolvedValue({ chunk: manyReactions });

    const result = await removeMatrixReactions(roomId, messageId);

    expect(result.removed).toBe(25);
    expect(mockClient.redactEvent).toHaveBeenCalledTimes(25);
  });
});

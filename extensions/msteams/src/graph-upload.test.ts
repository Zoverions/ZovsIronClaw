import { describe, expect, it, vi } from "vitest";
import { uploadToOneDrive, uploadToSharePoint } from "./graph-upload.js";

describe("graph-upload", () => {
  const tokenProvider = {
    getAccessToken: vi.fn(async () => "test-token"),
  };

  describe("uploadToOneDrive", () => {
    it("performs simple upload for small files", async () => {
      const fetchFn = vi.fn(async () => {
        return new Response(
          JSON.stringify({
            id: "item-id",
            webUrl: "https://web-url",
            name: "test.txt",
          }),
          { status: 200 },
        );
      });

      const buffer = Buffer.from("small file content");
      const result = await uploadToOneDrive({
        buffer,
        filename: "test.txt",
        tokenProvider,
        fetchFn: fetchFn as unknown as typeof fetch,
      });

      expect(fetchFn).toHaveBeenCalledWith(
        expect.stringContaining("/me/drive/root:/OpenClawShared/test.txt:/content"),
        expect.objectContaining({
          method: "PUT",
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
          }),
        }),
      );
      expect(result.id).toBe("item-id");
    });

    it("performs resumable upload for large files (>4MB)", async () => {
      const largeBuffer = Buffer.alloc(5 * 1024 * 1024, "a");
      const fetchFn = vi.fn(async (url: string, init?: RequestInit) => {
        if (url.endsWith("/createUploadSession")) {
          return new Response(JSON.stringify({ uploadUrl: "https://upload-session-url" }), {
            status: 200,
          });
        }
        if (url === "https://upload-session-url") {
          if (init?.headers && (init.headers as Record<string, string>)["Content-Range"]?.includes("/5242880")) {
             // Mocking last chunk
             if ((init.headers as Record<string, string>)["Content-Range"]?.startsWith("bytes 3276800-5242879")) {
                return new Response(JSON.stringify({
                  id: "large-item-id",
                  webUrl: "https://web-url-large",
                  name: "large.txt",
                }), { status: 201 });
             }
             return new Response(JSON.stringify({}), { status: 202 });
          }
        }
        return new Response("Not Found", { status: 404 });
      });

      const result = await uploadToOneDrive({
        buffer: largeBuffer,
        filename: "large.txt",
        tokenProvider,
        fetchFn: fetchFn as unknown as typeof fetch,
      });

      expect(fetchFn).toHaveBeenCalledWith(
        expect.stringContaining("/me/drive/root:/OpenClawShared/large.txt:/createUploadSession"),
        expect.objectContaining({ method: "POST" }),
      );
      // At least 2 chunks for 5MB with 3.125MB chunk size (327680 * 10)
      expect(fetchFn).toHaveBeenCalledWith(
        "https://upload-session-url",
        expect.objectContaining({ method: "PUT" }),
      );
      expect(result.id).toBe("large-item-id");
    });
  });

  describe("uploadToSharePoint", () => {
    it("performs simple upload for small files", async () => {
      const fetchFn = vi.fn(async () => {
        return new Response(
          JSON.stringify({
            id: "item-id",
            webUrl: "https://web-url",
            name: "test.txt",
          }),
          { status: 200 },
        );
      });

      const buffer = Buffer.from("small file content");
      const result = await uploadToSharePoint({
        buffer,
        filename: "test.txt",
        siteId: "site-id",
        tokenProvider,
        fetchFn: fetchFn as unknown as typeof fetch,
      });

      expect(fetchFn).toHaveBeenCalledWith(
        expect.stringContaining("/sites/site-id/drive/root:/OpenClawShared/test.txt:/content"),
        expect.objectContaining({
          method: "PUT",
        }),
      );
      expect(result.id).toBe("item-id");
    });

    it("performs resumable upload for large files (>4MB)", async () => {
      const largeBuffer = Buffer.alloc(5 * 1024 * 1024, "a");
      const fetchFn = vi.fn(async (url: string, init?: RequestInit) => {
        if (url.endsWith("/createUploadSession")) {
          return new Response(JSON.stringify({ uploadUrl: "https://upload-session-url-sp" }), {
            status: 200,
          });
        }
        if (url === "https://upload-session-url-sp") {
           // Mocking chunks
           if (init?.headers && (init.headers as Record<string, string>)["Content-Range"]?.startsWith("bytes 3276800-5242879")) {
              return new Response(JSON.stringify({
                id: "large-sp-item-id",
                webUrl: "https://web-url-large-sp",
                name: "large-sp.txt",
              }), { status: 201 });
           }
           return new Response(JSON.stringify({}), { status: 202 });
        }
        return new Response("Not Found", { status: 404 });
      });

      const result = await uploadToSharePoint({
        buffer: largeBuffer,
        filename: "large-sp.txt",
        siteId: "site-id",
        tokenProvider,
        fetchFn: fetchFn as unknown as typeof fetch,
      });

      expect(fetchFn).toHaveBeenCalledWith(
        expect.stringContaining("/sites/site-id/drive/root:/OpenClawShared/large-sp.txt:/createUploadSession"),
        expect.objectContaining({ method: "POST" }),
      );
      expect(result.id).toBe("large-sp-item-id");
    });
  });
});

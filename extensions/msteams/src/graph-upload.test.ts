import { describe, expect, it, vi } from "vitest";
import * as graphUpload from "./graph-upload.js";
import type { MSTeamsAccessTokenProvider } from "./attachments/types.js";

// Mock the module functions to avoid actual API calls
vi.mock("./graph-upload", async () => {
  const actual = await vi.importActual<typeof import("./graph-upload")>("./graph-upload");
  return {
    ...actual,
    // We will spy on or mock specific functions in tests if needed,
    // but here we are testing the functions themselves, so we don't want to mock them out completely.
    // However, since we are testing internal logic that calls fetch, we should mock fetch.
  };
});

describe("graph-upload", () => {
  const tokenProvider: MSTeamsAccessTokenProvider = {
    getAccessToken: vi.fn(async () => "mock-token"),
  };

  describe("uploadToOneDrive", () => {
    it("uploads small files (<4MB) using simple upload", async () => {
      const buffer = Buffer.alloc(1024); // 1KB
      const fetchMock = vi.fn().mockImplementation(async (url: string, opts: RequestInit) => {
        if (url.includes("/content") && opts.method === "PUT") {
          return new Response(JSON.stringify({
            id: "file-id",
            webUrl: "https://web.url",
            name: "file.txt"
          }), { status: 201 });
        }
        return new Response("Not Found", { status: 404 });
      });

      const result = await graphUpload.uploadToOneDrive({
        buffer,
        filename: "file.txt",
        tokenProvider,
        fetchFn: fetchMock as unknown as typeof fetch,
      });

      expect(result).toEqual({
        id: "file-id",
        webUrl: "https://web.url",
        name: "file.txt",
      });
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("uploads large files (>4MB) using resumable upload session", async () => {
      const largeSize = 5 * 1024 * 1024; // 5MB
      const buffer = Buffer.alloc(largeSize);
      const uploadUrl = "https://graph.microsoft.com/upload-session";

      const fetchMock = vi.fn().mockImplementation(async (url: string, opts: RequestInit) => {
        // 1. Create upload session
        if (url.includes("createUploadSession") && opts.method === "POST") {
          return new Response(JSON.stringify({ uploadUrl }), { status: 200 });
        }

        // 2. Upload chunks
        if (url === uploadUrl && opts.method === "PUT") {
          const rangeHeader = (opts.headers as any)["Content-Range"];
          if (!rangeHeader) return new Response("Missing Content-Range", { status: 400 });

          const match = rangeHeader.match(/bytes (\d+)-(\d+)\/(\d+)/);
          if (!match) return new Response("Invalid Content-Range", { status: 400 });

          const start = parseInt(match[1]);
          const end = parseInt(match[2]);
          const total = parseInt(match[3]);

          if (end === total - 1) {
             return new Response(JSON.stringify({
              id: "large-file-id",
              webUrl: "https://large.web.url",
              name: "large.txt"
            }), { status: 201 });
          }
           return new Response(JSON.stringify({
            nextExpectedRanges: [`${end + 1}-`]
          }), { status: 202 });
        }

        return new Response("Not Found", { status: 404 });
      });

      const result = await graphUpload.uploadToOneDrive({
        buffer,
        filename: "large.txt",
        tokenProvider,
        fetchFn: fetchMock as unknown as typeof fetch,
      });

      expect(result).toEqual({
        id: "large-file-id",
        webUrl: "https://large.web.url",
        name: "large.txt",
      });

      // Verification:
      // 1 call to create session
      // 2 chunks (since 5MB > 4MB threshold, and likely chunk size is < 5MB)
      // If chunk size is 3.2MB (10 * 320KB), then 5MB will be split into 3.2MB + 1.8MB
      expect(fetchMock).toHaveBeenCalled();
      const calls = fetchMock.mock.calls;
      const createSessionCall = calls.find(c => c[0].includes("createUploadSession"));
      expect(createSessionCall).toBeDefined();
    });
  });

  describe("uploadToSharePoint", () => {
    it("uploads small files (<4MB) using simple upload", async () => {
      const buffer = Buffer.alloc(1024);
      const fetchMock = vi.fn().mockImplementation(async (url: string, opts: RequestInit) => {
         if (url.includes("/content") && opts.method === "PUT") {
          return new Response(JSON.stringify({
            id: "sp-file-id",
            webUrl: "https://sp.web.url",
            name: "sp-file.txt"
          }), { status: 201 });
        }
        return new Response("Not Found", { status: 404 });
      });

      const result = await graphUpload.uploadToSharePoint({
        buffer,
        filename: "sp-file.txt",
        siteId: "site-id",
        tokenProvider,
        fetchFn: fetchMock as unknown as typeof fetch,
      });

      expect(result).toEqual({
        id: "sp-file-id",
        webUrl: "https://sp.web.url",
        name: "sp-file.txt",
      });
    });

    it("uploads large files (>4MB) using resumable upload session", async () => {
      const largeSize = 5 * 1024 * 1024; // 5MB
      const buffer = Buffer.alloc(largeSize);
      const uploadUrl = "https://graph.microsoft.com/upload-session-sp";

       const fetchMock = vi.fn().mockImplementation(async (url: string, opts: RequestInit) => {
        // 1. Create upload session
        if (url.includes("createUploadSession") && opts.method === "POST") {
          return new Response(JSON.stringify({ uploadUrl }), { status: 200 });
        }

        // 2. Upload chunks
        if (url === uploadUrl && opts.method === "PUT") {
          const rangeHeader = (opts.headers as any)["Content-Range"];
          if (!rangeHeader) return new Response("Missing Content-Range", { status: 400 });

          const match = rangeHeader.match(/bytes (\d+)-(\d+)\/(\d+)/);
          const end = parseInt(match![2]);
          const total = parseInt(match![3]);

          if (end === total - 1) {
             return new Response(JSON.stringify({
              id: "large-sp-file-id",
              webUrl: "https://large.sp.web.url",
              name: "large-sp.txt"
            }), { status: 201 });
          }
           return new Response(JSON.stringify({
            nextExpectedRanges: [`${end + 1}-`]
          }), { status: 202 });
        }

        return new Response("Not Found", { status: 404 });
      });

      const result = await graphUpload.uploadToSharePoint({
        buffer,
        filename: "large-sp.txt",
        siteId: "site-id",
        tokenProvider,
        fetchFn: fetchMock as unknown as typeof fetch,
      });

      expect(result).toEqual({
        id: "large-sp-file-id",
        webUrl: "https://large.sp.web.url",
        name: "large-sp.txt",
      });

      const calls = fetchMock.mock.calls;
      const createSessionCall = calls.find(c => c[0].includes("createUploadSession"));
      expect(createSessionCall).toBeDefined();
    });
  });
});

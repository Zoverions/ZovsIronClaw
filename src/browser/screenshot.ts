import { getImageMetadata, resizeToJpeg } from "../media/image-ops.js";

export const DEFAULT_BROWSER_SCREENSHOT_MAX_SIDE = 2000;
export const DEFAULT_BROWSER_SCREENSHOT_MAX_BYTES = 5 * 1024 * 1024;

export async function normalizeBrowserScreenshot(
  buffer: Buffer,
  opts?: {
    maxSide?: number;
    maxBytes?: number;
  },
): Promise<{ buffer: Buffer; contentType?: "image/jpeg" }> {
  const maxSide = Math.max(1, Math.round(opts?.maxSide ?? DEFAULT_BROWSER_SCREENSHOT_MAX_SIDE));
  const maxBytes = Math.max(1, Math.round(opts?.maxBytes ?? DEFAULT_BROWSER_SCREENSHOT_MAX_BYTES));

  const meta = await getImageMetadata(buffer);
  const width = Number(meta?.width ?? 0);
  const height = Number(meta?.height ?? 0);
  const maxDim = Math.max(width, height);

  if (buffer.byteLength <= maxBytes && (maxDim === 0 || (width <= maxSide && height <= maxSide))) {
    return { buffer };
  }

  const qualities = [85, 75, 65, 55, 45, 35];
  const sideStart = maxDim > 0 ? Math.min(maxSide, maxDim) : maxSide;
  const sideGrid = [sideStart, 1800, 1600, 1400, 1200, 1000, 800]
    .map((v) => Math.min(maxSide, v))
    .filter((v, i, arr) => v > 0 && arr.indexOf(v) === i)
    .toSorted((a, b) => b - a);

  let smallest: { buffer: Buffer; size: number } | null = null;

  for (const side of sideGrid) {
    // Optimization: Check the best (highest quality) and worst (lowest quality)
    // first to prune the search space.

    // 1. Try highest quality (85)
    const outBest = await resizeToJpeg({
      buffer,
      maxSide: side,
      quality: qualities[0],
      withoutEnlargement: true,
    });

    if (!smallest || outBest.byteLength < smallest.size) {
      smallest = { buffer: outBest, size: outBest.byteLength };
    }

    if (outBest.byteLength <= maxBytes) {
      return { buffer: outBest, contentType: "image/jpeg" };
    }

    // 2. Try lowest quality (35)
    // If even the lowest quality is too big, skip all intermediate qualities for this size.
    const outWorst = await resizeToJpeg({
      buffer,
      maxSide: side,
      quality: qualities[qualities.length - 1],
      withoutEnlargement: true,
    });

    if (!smallest || outWorst.byteLength < smallest.size) {
      smallest = { buffer: outWorst, size: outWorst.byteLength };
    }

    if (outWorst.byteLength > maxBytes) {
      // Pruning: Lowest quality is still too big, so skip intermediate qualities.
      continue;
    }

    // 3. Lowest quality fits, but highest didn't. Search intermediate qualities.
    // We already checked qualities[0] (85) and qualities[length-1] (35).
    // Iterate through the rest: 75, 65, 55, 45
    for (let i = 1; i < qualities.length - 1; i++) {
      const quality = qualities[i];
      const out = await resizeToJpeg({
        buffer,
        maxSide: side,
        quality,
        withoutEnlargement: true,
      });

      if (!smallest || out.byteLength < smallest.size) {
        smallest = { buffer: out, size: out.byteLength };
      }

      if (out.byteLength <= maxBytes) {
        return { buffer: out, contentType: "image/jpeg" };
      }
    }

    // If we get here, intermediate qualities failed but lowest quality (35) passed.
    // Return the lowest quality result we already computed.
    return { buffer: outWorst, contentType: "image/jpeg" };
  }

  const best = smallest?.buffer ?? buffer;
  throw new Error(
    `Browser screenshot could not be reduced below ${(maxBytes / (1024 * 1024)).toFixed(0)}MB (got ${(best.byteLength / (1024 * 1024)).toFixed(2)}MB)`,
  );
}

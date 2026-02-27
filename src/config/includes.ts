/**
 * Config includes: $include directive for modular configs
 *
 * @example
 * ```json5
 * {
 *   "$include": "./base.json5",           // single file
 *   "$include": ["./a.json5", "./b.json5"] // merge multiple
 * }
 * ```
 */

import JSON5 from "json5";
import fs from "node:fs";
import path from "node:path";

export const INCLUDE_KEY = "$include";
export const MAX_INCLUDE_DEPTH = 10;

// ============================================================================
// Types
// ============================================================================

export type IncludeResolver = {
  readFile: (path: string) => string;
  parseJson: (raw: string) => unknown;
};

export type IncludeResolverAsync = {
  readFile: (path: string) => Promise<string>;
  parseJson: (raw: string) => unknown;
};

// ============================================================================
// Errors
// ============================================================================

export class ConfigIncludeError extends Error {
  constructor(
    message: string,
    public readonly includePath: string,
    public readonly cause?: Error,
  ) {
    super(message);
    this.name = "ConfigIncludeError";
  }
}

export class CircularIncludeError extends ConfigIncludeError {
  constructor(public readonly chain: string[]) {
    super(`Circular include detected: ${chain.join(" -> ")}`, chain[chain.length - 1]);
    this.name = "CircularIncludeError";
  }
}

// ============================================================================
// Utilities
// ============================================================================

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    Object.prototype.toString.call(value) === "[object Object]"
  );
}

/** Deep merge: arrays concatenate, objects merge recursively, primitives: source wins */
export function deepMerge(target: unknown, source: unknown): unknown {
  if (Array.isArray(target) && Array.isArray(source)) {
    return [...target, ...source];
  }
  if (isPlainObject(target) && isPlainObject(source)) {
    const result: Record<string, unknown> = { ...target };
    for (const key of Object.keys(source)) {
      result[key] = key in result ? deepMerge(result[key], source[key]) : source[key];
    }
    return result;
  }
  return source;
}

// ============================================================================
// Include Resolver Class
// ============================================================================

class IncludeProcessor {
  private visited = new Set<string>();
  private depth = 0;

  constructor(
    private basePath: string,
    private resolver: IncludeResolver | IncludeResolverAsync,
  ) {
    this.visited.add(path.normalize(basePath));
  }

  process(obj: unknown): unknown {
    if (this.isAsync()) {
      throw new Error("Cannot call synchronous process() with an async resolver");
    }
    return this.processSync(obj);
  }

  async processAsync(obj: unknown): Promise<unknown> {
    if (Array.isArray(obj)) {
      return Promise.all(obj.map((item) => this.processAsync(item)));
    }

    if (!isPlainObject(obj)) {
      return obj;
    }

    if (!(INCLUDE_KEY in obj)) {
      return this.processObjectAsync(obj);
    }

    return this.processIncludeAsync(obj);
  }

  private isAsync(): boolean {
    const r = this.resolver as IncludeResolverAsync;
    // Simple heuristic: if readFile returns a Promise, it's async.
    // However, since we define types, we can assume the caller uses the right method.
    // But `this.resolver` is a union.
    // For now, let's rely on methods `process` vs `processAsync`.
    // The issue is `process` calls `this.resolver.readFile` which might be async.
    return false; // Type safety handles this in the public API wrappers.
  }

  // --- Synchronous Implementation ---

  private processSync(obj: unknown): unknown {
    if (Array.isArray(obj)) {
      return obj.map((item) => this.processSync(item));
    }

    if (!isPlainObject(obj)) {
      return obj;
    }

    if (!(INCLUDE_KEY in obj)) {
      return this.processObjectSync(obj);
    }

    return this.processIncludeSync(obj);
  }

  private processObjectSync(obj: Record<string, unknown>): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = this.processSync(value);
    }
    return result;
  }

  private processIncludeSync(obj: Record<string, unknown>): unknown {
    const includeValue = obj[INCLUDE_KEY];
    const otherKeys = Object.keys(obj).filter((k) => k !== INCLUDE_KEY);
    const included = this.resolveIncludeSync(includeValue);

    if (otherKeys.length === 0) {
      return included;
    }

    if (!isPlainObject(included)) {
      throw new ConfigIncludeError(
        "Sibling keys require included content to be an object",
        typeof includeValue === "string" ? includeValue : INCLUDE_KEY,
      );
    }

    const rest: Record<string, unknown> = {};
    for (const key of otherKeys) {
      rest[key] = this.processSync(obj[key]);
    }
    return deepMerge(included, rest);
  }

  private resolveIncludeSync(value: unknown): unknown {
    if (typeof value === "string") {
      return this.loadFileSync(value);
    }

    if (Array.isArray(value)) {
      return value.reduce<unknown>((merged, item) => {
        if (typeof item !== "string") {
          throw new ConfigIncludeError(
            `Invalid $include array item: expected string, got ${typeof item}`,
            String(item),
          );
        }
        return deepMerge(merged, this.loadFileSync(item));
      }, {});
    }

    throw new ConfigIncludeError(
      `Invalid $include value: expected string or array of strings, got ${typeof value}`,
      String(value),
    );
  }

  private loadFileSync(includePath: string): unknown {
    const resolvedPath = this.resolvePath(includePath);
    this.checkCircular(resolvedPath);
    this.checkDepth(includePath);

    const raw = this.readFileSync(includePath, resolvedPath);
    const parsed = this.parseFile(includePath, resolvedPath, raw);

    return this.processNestedSync(resolvedPath, parsed);
  }

  private readFileSync(includePath: string, resolvedPath: string): string {
    try {
      return (this.resolver as IncludeResolver).readFile(resolvedPath);
    } catch (err) {
      throw new ConfigIncludeError(
        `Failed to read include file: ${includePath} (resolved: ${resolvedPath})`,
        includePath,
        err instanceof Error ? err : undefined,
      );
    }
  }

  private processNestedSync(resolvedPath: string, parsed: unknown): unknown {
    const nested = new IncludeProcessor(resolvedPath, this.resolver);
    nested.visited = new Set([...this.visited, resolvedPath]);
    nested.depth = this.depth + 1;
    return nested.processSync(parsed);
  }

  // --- Async Implementation ---

  private async processObjectAsync(obj: Record<string, unknown>): Promise<Record<string, unknown>> {
    const result: Record<string, unknown> = {};
    // Process keys in parallel
    const entries = Object.entries(obj);
    const values = await Promise.all(entries.map(([, value]) => this.processAsync(value)));
    for (let i = 0; i < entries.length; i++) {
      result[entries[i][0]] = values[i];
    }
    return result;
  }

  private async processIncludeAsync(obj: Record<string, unknown>): Promise<unknown> {
    const includeValue = obj[INCLUDE_KEY];
    const otherKeys = Object.keys(obj).filter((k) => k !== INCLUDE_KEY);
    const included = await this.resolveIncludeAsync(includeValue);

    if (otherKeys.length === 0) {
      return included;
    }

    if (!isPlainObject(included)) {
      throw new ConfigIncludeError(
        "Sibling keys require included content to be an object",
        typeof includeValue === "string" ? includeValue : INCLUDE_KEY,
      );
    }

    const rest: Record<string, unknown> = {};
    // Process other keys in parallel
    const values = await Promise.all(otherKeys.map((key) => this.processAsync(obj[key])));
    for (let i = 0; i < otherKeys.length; i++) {
      rest[otherKeys[i]] = values[i];
    }
    return deepMerge(included, rest);
  }

  private async resolveIncludeAsync(value: unknown): Promise<unknown> {
    if (typeof value === "string") {
      return this.loadFileAsync(value);
    }

    if (Array.isArray(value)) {
      // Process includes sequentially to respect order (later includes override earlier ones)
      // Though deepMerge is commutative for disjoint sets, it matters for overlaps.
      // reduce is synchronous, so we need an async reduce equivalent.
      let merged: unknown = {};
      for (const item of value) {
        if (typeof item !== "string") {
          throw new ConfigIncludeError(
            `Invalid $include array item: expected string, got ${typeof item}`,
            String(item),
          );
        }
        const loaded = await this.loadFileAsync(item);
        merged = deepMerge(merged, loaded);
      }
      return merged;
    }

    throw new ConfigIncludeError(
      `Invalid $include value: expected string or array of strings, got ${typeof value}`,
      String(value),
    );
  }

  private async loadFileAsync(includePath: string): Promise<unknown> {
    const resolvedPath = this.resolvePath(includePath);
    this.checkCircular(resolvedPath);
    this.checkDepth(includePath);

    const raw = await this.readFileAsync(includePath, resolvedPath);
    const parsed = this.parseFile(includePath, resolvedPath, raw);

    return this.processNestedAsync(resolvedPath, parsed);
  }

  private async readFileAsync(includePath: string, resolvedPath: string): Promise<string> {
    try {
      return await (this.resolver as IncludeResolverAsync).readFile(resolvedPath);
    } catch (err) {
      throw new ConfigIncludeError(
        `Failed to read include file: ${includePath} (resolved: ${resolvedPath})`,
        includePath,
        err instanceof Error ? err : undefined,
      );
    }
  }

  private processNestedAsync(resolvedPath: string, parsed: unknown): Promise<unknown> {
    const nested = new IncludeProcessor(resolvedPath, this.resolver);
    nested.visited = new Set([...this.visited, resolvedPath]);
    nested.depth = this.depth + 1;
    return nested.processAsync(parsed);
  }

  // --- Shared ---

  private resolvePath(includePath: string): string {
    const resolved = path.isAbsolute(includePath)
      ? includePath
      : path.resolve(path.dirname(this.basePath), includePath);
    return path.normalize(resolved);
  }

  private checkCircular(resolvedPath: string): void {
    if (this.visited.has(resolvedPath)) {
      throw new CircularIncludeError([...this.visited, resolvedPath]);
    }
  }

  private checkDepth(includePath: string): void {
    if (this.depth >= MAX_INCLUDE_DEPTH) {
      throw new ConfigIncludeError(
        `Maximum include depth (${MAX_INCLUDE_DEPTH}) exceeded at: ${includePath}`,
        includePath,
      );
    }
  }

  private parseFile(includePath: string, resolvedPath: string, raw: string): unknown {
    try {
      return this.resolver.parseJson(raw);
    } catch (err) {
      throw new ConfigIncludeError(
        `Failed to parse include file: ${includePath} (resolved: ${resolvedPath})`,
        includePath,
        err instanceof Error ? err : undefined,
      );
    }
  }
}

// ============================================================================
// Public API
// ============================================================================

const defaultResolver: IncludeResolver = {
  readFile: (p) => fs.readFileSync(p, "utf-8"),
  parseJson: (raw) => JSON5.parse(raw),
};

const defaultResolverAsync: IncludeResolverAsync = {
  readFile: (p) => fs.promises.readFile(p, "utf-8"),
  parseJson: (raw) => JSON5.parse(raw),
};

/**
 * Resolves all $include directives in a parsed config object.
 */
export function resolveConfigIncludes(
  obj: unknown,
  configPath: string,
  resolver: IncludeResolver = defaultResolver,
): unknown {
  return new IncludeProcessor(configPath, resolver).process(obj);
}

/**
 * Resolves all $include directives in a parsed config object asynchronously.
 */
export function resolveConfigIncludesAsync(
  obj: unknown,
  configPath: string,
  resolver: IncludeResolverAsync = defaultResolverAsync,
): Promise<unknown> {
  return new IncludeProcessor(configPath, resolver).processAsync(obj);
}

import type { ProviderPlugin } from "./types.js";
import { normalizeProviderId } from "../agents/model-selection.js";
import { createSubsystemLogger } from "../logging/subsystem.js";
import { loadOpenClawPlugins, type PluginLoadOptions } from "./loader.js";

const log = createSubsystemLogger("plugins");

export function buildProviderMap(providers: ProviderPlugin[]): Map<string, ProviderPlugin> {
  const map = new Map<string, ProviderPlugin>();
  // First pass: map IDs. The first provider with a given ID wins.
  for (const provider of providers) {
    const id = normalizeProviderId(provider.id);
    if (!map.has(id)) {
      map.set(id, provider);
    }
  }
  // Second pass: map aliases. Only map if the key is not already taken by an ID or previous alias.
  for (const provider of providers) {
    if (provider.aliases) {
      for (const alias of provider.aliases) {
        const normalizedAlias = normalizeProviderId(alias);
        if (!map.has(normalizedAlias)) {
          map.set(normalizedAlias, provider);
        }
      }
    }
  }
  return map;
}

export function resolvePluginProviders(params: {
  config?: PluginLoadOptions["config"];
  workspaceDir?: string;
}): ProviderPlugin[] {
  const registry = loadOpenClawPlugins({
    config: params.config,
    workspaceDir: params.workspaceDir,
    logger: {
      info: (msg) => log.info(msg),
      warn: (msg) => log.warn(msg),
      error: (msg) => log.error(msg),
      debug: (msg) => log.debug(msg),
    },
  });

  return registry.providers.map((entry) => entry.provider);
}

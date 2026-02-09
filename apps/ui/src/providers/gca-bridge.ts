// GCA Bridge: TypeScript Provider for connecting to GCA Service
// ---------------------------------------------------------------
// Handles:
// 1. Connection (Direct REST in Web, Tauri Invoke in Desktop)
// 2. Resource Awareness (Does it fallback to API?)

export interface GCAConfig {
    serviceUrl: string;
    riskTolerance: number;
}

export interface GCARequest {
    user_id: string;
    text: string;
    soul_config?: string;
    tools_available?: string[];
}

export interface GCAResponse {
    status: string;
    content: string;
    meta?: any;
    tool_call?: { name: string, args: string };
}

export interface SoulConfig {
    base_style: string;
    blend_styles: string[];
    blend_weights: number[];
}

export interface SoulInfo {
    name: string;
    description: string;
    entropy_tolerance?: string;
    risk_tolerance?: number;
    traits?: string[];
}

const invoke = async (cmd: string, args?: any) => {
    if ((window as any).__TAURI__?.core) {
        return (window as any).__TAURI__.core.invoke(cmd, args);
    }
    return null;
};

export class GCAProvider {
    config: GCAConfig;
    isDesktop: boolean;

    constructor(config: GCAConfig) {
        this.config = config;
        this.isDesktop = !!(window as any).__TAURI__;
    }

    async reason(req: GCARequest): Promise<GCAResponse> {
        // If Desktop: Use Tauri Sidecar Proxy (if implemented) or localhost
        // For now, Sidecar exposes on localhost:8000 so we fetch

        try {
            const response = await fetch(`${this.config.serviceUrl}/v1/reason`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(req)
            });

            if (!response.ok) {
                throw new Error(`GCA Service Error: ${response.statusText}`);
            }

            const result: GCAResponse = await response.json();

            // Handle Tool Execution (Computer Use)
            if (this.isDesktop && result.tool_call && result.status !== "BLOCKED") {
                const tool = result.tool_call;
                // Check if tool is a shell command
                if (['bash', 'sh', 'cmd', 'powershell'].includes(tool.name)) {
                    try {
                        console.log(`[GCA] Executing shell command: ${tool.args}`);
                        const output = await invoke('execute_shell_command', { command: tool.args });

                        // Append output to content so user sees the result
                        result.content += `\n\n> [EXECUTION OUTPUT]\n${output}`;
                    } catch (e) {
                         console.error(`[GCA] Execution Error: ${e}`);
                         result.content += `\n\n> [EXECUTION ERROR]\n${e}`;
                    }
                }
            }

            return result;
        } catch (e) {
            console.error("GCA Reasoning Failed", e);
            // Fallback Logic could go here (e.g., call Cloud LLM directly if local failed)
            return {
                status: "ERROR",
                content: "I'm having trouble connecting to my neural core. Is the service running?",
                meta: { error: String(e) }
            };
        }
    }

    async listSouls(): Promise<{ souls: string[], details: Record<string, SoulInfo> }> {
        try {
            const response = await fetch(`${this.config.serviceUrl}/v1/soul/list`);
            if (!response.ok) throw new Error(`GCA Service Error: ${response.statusText}`);
            return await response.json();
        } catch (e) {
            console.error("Failed to list souls", e);
            throw e;
        }
    }

    async composeSoul(config: SoulConfig): Promise<any> {
        try {
            const response = await fetch(`${this.config.serviceUrl}/v1/soul/compose`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            if (!response.ok) throw new Error(`GCA Service Error: ${response.statusText}`);
            return await response.json();
        } catch (e) {
             console.error("Failed to compose soul", e);
             throw e;
        }
    }
}

export const createGCAProvider = (config: GCAConfig) => new GCAProvider(config);

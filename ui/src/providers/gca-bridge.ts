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
}

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

            return await response.json();
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
}

export const createGCAProvider = (config: GCAConfig) => new GCAProvider(config);

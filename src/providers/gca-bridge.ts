/**
 * GCA Bridge Provider
 * Connects OpenClaw to the GCA (Geometric Conscience Architecture) service
 * Provides ethical AI reasoning with geometric steering and moral evaluation
 */

import type { Message, Tool, ToolCall } from "../types/index.js";

export interface GCAConfig {
  serviceUrl: string;
  riskTolerance?: number;
  useQPT?: boolean;
  defaultSoul?: string;
}

export interface GCAReasoningRequest {
  user_id: string;
  text: string;
  tools_available: string[];
  context?: string;
  soul_name?: string;
  use_qpt?: boolean;
}

export interface GCAReasoningResponse {
  status: "APPROVED" | "BLOCKED";
  response: string;
  tool_call?: {
    name: string;
    args: any;
    confidence: number;
  };
  moral_signature?: string;
  risk_score: number;
  reasoning_path: string[];
}

/**
 * GCA Bridge Provider for OpenClaw
 * Routes all reasoning through the GCA moral kernel
 */
export class GCABridgeProvider {
  private config: GCAConfig;
  private serviceUrl: string;

  constructor(config: Partial<GCAConfig> = {}) {
    this.config = {
      serviceUrl: config.serviceUrl || process.env.GCA_SERVICE_URL || "http://gca-service:8000",
      riskTolerance: config.riskTolerance || 0.3,
      useQPT: config.useQPT !== false, // Default true
      defaultSoul: config.defaultSoul || undefined,
    };
    this.serviceUrl = this.config.serviceUrl;
  }

  /**
   * Main chat interface - routes through GCA pipeline
   */
  async chat(params: {
    messages: Message[];
    tools?: Tool[];
    userId?: string;
    context?: string;
    soulName?: string;
  }): Promise<Message> {
    const { messages, tools = [], userId = "default", context, soulName } = params;

    // Extract the latest user message
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage || lastMessage.role !== "user") {
      throw new Error("Last message must be from user");
    }

    const userText = typeof lastMessage.content === "string" 
      ? lastMessage.content 
      : lastMessage.content.map(c => c.type === "text" ? c.text : "").join(" ");

    // Prepare request for GCA service
    const request: GCAReasoningRequest = {
      user_id: userId,
      text: userText,
      tools_available: tools.map(t => t.name),
      context,
      soul_name: soulName || this.config.defaultSoul,
      use_qpt: this.config.useQPT,
    };

    try {
      // Call GCA reasoning endpoint
      const response = await this.callGCAService("/v1/reason", request);

      // Handle moral block
      if (response.status === "BLOCKED") {
        return {
          role: "assistant",
          content: `🛡️ [MORAL KERNEL INTERVENTION]\n\n${response.response}\n\n_Risk Score: ${response.risk_score.toFixed(2)}_`,
        };
      }

      // Handle approved response with tool call
      if (response.tool_call && response.moral_signature) {
        const toolCalls: ToolCall[] = [
          {
            id: this.generateToolCallId(),
            type: "function",
            function: {
              name: response.tool_call.name,
              arguments: JSON.stringify(response.tool_call.args),
            },
            // Store moral signature in metadata for verification
            _gcaSignature: response.moral_signature,
          },
        ];

        return {
          role: "assistant",
          content: response.response,
          tool_calls: toolCalls,
        };
      }

      // Standard approved response
      return {
        role: "assistant",
        content: response.response,
      };
    } catch (error) {
      console.error("[GCA Bridge] Error:", error);
      // Fallback to safe error message
      return {
        role: "assistant",
        content: `I encountered an error while processing your request through the GCA framework. Error: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  }

  /**
   * Verify moral signature before tool execution
   */
  async verifyMoralSignature(toolCall: ToolCall): Promise<boolean> {
    const signature = (toolCall as any)._gcaSignature;
    if (!signature) {
      console.warn("[GCA Bridge] No moral signature found on tool call - BLOCKING");
      return false;
    }

    // In production, verify the signature cryptographically
    // For now, presence of signature indicates approval
    return true;
  }

  /**
   * Run Arena Protocol for testing
   */
  async runArena(rounds: number = 10): Promise<any> {
    try {
      const response = await fetch(`${this.serviceUrl}/v1/arena/run?rounds=${rounds}`);
      if (!response.ok) {
        throw new Error(`Arena failed: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("[GCA Bridge] Arena error:", error);
      throw error;
    }
  }

  /**
   * Get service health status
   */
  async getHealth(): Promise<any> {
    try {
      const response = await fetch(`${this.serviceUrl}/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("[GCA Bridge] Health check error:", error);
      throw error;
    }
  }

  /**
   * Call GCA service endpoint
   */
  private async callGCAService(
    endpoint: string,
    data: any
  ): Promise<GCAReasoningResponse> {
    const url = `${this.serviceUrl}${endpoint}`;
    
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`GCA Service error (${response.status}): ${errorText}`);
    }

    return await response.json();
  }

  /**
   * Generate unique tool call ID
   */
  private generateToolCallId(): string {
    return `gca_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

/**
 * Factory function for creating GCA provider
 */
export function createGCAProvider(config?: Partial<GCAConfig>): GCABridgeProvider {
  return new GCABridgeProvider(config);
}

/**
 * Middleware for tool execution verification
 * Ensures all tool calls have moral approval
 */
export async function verifyToolExecution(
  toolCall: ToolCall,
  provider: GCABridgeProvider
): Promise<void> {
  const isApproved = await provider.verifyMoralSignature(toolCall);
  
  if (!isApproved) {
    throw new Error(
      `[MORAL KERNEL BLOCK] Tool execution denied: Missing or invalid moral authorization. ` +
      `All tool executions must be approved by the GCA Moral Kernel.`
    );
  }
}

export default GCABridgeProvider;

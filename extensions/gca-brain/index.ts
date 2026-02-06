import { Service } from '../../src/gateway/service';
import { ModelProvider, ChatContext, ChatResponse } from '../../src/types/models';

export default class GCAProvider extends Service implements ModelProvider {
  name = 'gca-ironclaw';
  id = 'gca-local';

  async generateResponse(context: ChatContext): Promise<ChatResponse> {
    const userMessage = context.lastMessage.text;

    // 1. Get the Soul configuration from the Agent's file
    // OpenClaw loads .agent/prompts/SOUL.md into memory
    const soulConfig = context.agent.prompts?.find((p: any) => p.id === 'SOUL')?.text || "";

    try {
      // 2. Call the Python Brain
      const apiUrl = process.env.GCA_API_URL || 'http://gca-service:8000';
      const response = await fetch(`${apiUrl}/v1/reason`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: context.user.id,
          text: userMessage,
          soul_config: soulConfig,
          input_modality: context.inputType || 'text'
        })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();

      // 3. Return to OpenClaw User
      // Handle Moral Refusal
      if (data.status === 'BLOCKED') {
        return { text: `[SYSTEM HALT] ${data.content}` };
      }

      // Handle Approved Tool Call
      if (data.tool_call) {
        // We inject the moral signature (token) into the arguments
        // This effectively "stamps" the tool call with approval
        // The tool runner policy will verify this stamp.
        let args = data.tool_call.args;

        // Ensure args is an object
        if (typeof args === 'string') {
            try { args = JSON.parse(args); } catch(e) {}
        }
        if (typeof args !== 'object' || args === null) {
            args = { _raw_args: args };
        }

        // Inject Token
        if (data.moral_signature) {
            args._gca_token = data.moral_signature;
        }

        return {
            text: data.content || "Executing approved action...",
            toolCalls: [{
                name: data.tool_call.name,
                arguments: args
            }]
        } as any; // Cast to any to avoid type check issues in this environment
      }

      return {
        text: data.content,
        usage: { inputTokens: 0, outputTokens: 0 }
      };

    } catch (err) {
      this.logger.error(`GCA Connection Error: ${err}`);
      return { text: `[GCA CONNECTION ERROR] Is the Brain container running? ${err}` };
    }
  }
}

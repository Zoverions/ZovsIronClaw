import { Service } from '../../src/gateway/service';
import { ModelProvider, ChatContext, ChatResponse } from '../../src/types/models';

function envEnabled(name: string): boolean {
  return ['1', 'true', 'yes', 'on'].includes((process.env[name] || '').trim().toLowerCase());
}

export default class GCAProvider extends Service implements ModelProvider {
  name = 'gca-ironclaw';
  id = 'gca-local';

  async generateResponse(context: ChatContext): Promise<ChatResponse> {
    const userMessage = context.lastMessage.text;

    // GCA is an experimental advisory provider. It does not get an implicit
    // execution capability merely because a heuristic policy layer approved text.
    const apiKey = process.env.GCA_API_KEY;
    if (!apiKey) {
      return {
        text: '[GCA DISABLED] GCA_API_KEY is not configured. The experimental GCA provider fails closed.',
      };
    }

    // 1. Get the Soul configuration from the Agent's file.
    // OpenClaw loads .agent/prompts/SOUL.md into memory.
    const soulConfig = context.agent.prompts?.find((p: any) => p.id === 'SOUL')?.text || '';

    try {
      // 2. Call the Python Brain through the authenticated local/service boundary.
      const apiUrl = process.env.GCA_API_URL || 'http://gca-service:8000';
      const response = await fetch(`${apiUrl}/v1/reason`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GCA-API-Key': apiKey,
        },
        body: JSON.stringify({
          user_id: context.user.id,
          text: userMessage,
          soul_config: soulConfig,
          input_modality: context.inputType || 'text',
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      // 3. Return advisory output to OpenClaw.
      if (data.status === 'BLOCKED') {
        return { text: `[GCA ADVISORY] ${data.content}` };
      }

      if (data.tool_call) {
        const toolName = typeof data.tool_call.name === 'string' ? data.tool_call.name : 'unknown';

        // Default-deny: a GCA moral/entropy/thermodynamic score or signature is not
        // an execution authorization. Experimental tool-call forwarding must be
        // explicitly enabled and remains subject to the normal OpenClaw tool policy.
        if (!envEnabled('GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS')) {
          return {
            text:
              `[GCA ADVISORY] Suggested tool call '${toolName}' was not forwarded. ` +
              'Set GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS=1 only for isolated evaluation.',
          };
        }

        let args = data.tool_call.args;
        if (typeof args === 'string') {
          try {
            args = JSON.parse(args);
          } catch {
            // Preserve malformed/raw arguments as inert data for the normal tool layer.
          }
        }
        if (typeof args !== 'object' || args === null) {
          args = { _raw_args: args };
        }

        return {
          text: data.content || '[GCA ADVISORY] Experimental tool suggestion forwarded for normal policy handling.',
          toolCalls: [
            {
              name: toolName,
              arguments: args,
            },
          ],
        } as any;
      }

      return {
        text: data.content,
        usage: { inputTokens: 0, outputTokens: 0 },
      };
    } catch (err) {
      this.logger.error(`GCA Connection Error: ${err}`);
      return { text: `[GCA CONNECTION ERROR] Experimental provider unavailable: ${err}` };
    }
  }
}

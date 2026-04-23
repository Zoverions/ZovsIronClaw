import { linePlugin } from "./extensions/line/src/channel.js";
import { setLineRuntime } from "./extensions/line/src/runtime.js";

async function run() {
  const accountId = "default";

  // Create a mock processed object since we mock processLineMessage
  // Actually linePlugin.outbound.sendText imports processLineMessage from openclaw/plugin-sdk.
  // We can just pass text that results in multiple flex messages.
  // Wait, processLineMessage parses tables into flex messages.

  const text = `
| A | B |
|---|---|
| 1 | 2 |

| C | D |
|---|---|
| 3 | 4 |

| E | F |
|---|---|
| 5 | 6 |

| G | H |
|---|---|
| 7 | 8 |

| I | J |
|---|---|
| 9 | 10 |

| K | L |
|---|---|
| 11 | 12 |
  `;

  // Mock the runtime
  const runtime = {
    channel: {
      line: {
        pushMessageLine: async () => {
          await new Promise(r => setTimeout(r, 50));
          return { messageId: "msg1", chatId: "to1" };
        },
        pushFlexMessage: async () => {
          await new Promise(r => setTimeout(r, 50));
          return { messageId: "flex1", chatId: "to1" };
        }
      }
    }
  };
  setLineRuntime(runtime as any);

  const start = Date.now();
  await linePlugin.outbound!.sendText!({
    to: "user1",
    text,
    accountId,
    cfg: {} as any
  });
  const end = Date.now();
  console.log(`Time taken: ${end - start}ms`);
}

run().catch(console.error);

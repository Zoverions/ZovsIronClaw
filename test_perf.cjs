const fs = require('fs');

async function mockSendMessage(chatId, chunk) {
  return new Promise(resolve => setTimeout(resolve, 50));
}

async function runSequential(chunks) {
  const start = Date.now();
  for (const chunk of chunks) {
    await mockSendMessage('chatId', chunk);
  }
  return Date.now() - start;
}

async function runConcurrent(chunks, limit) {
  const start = Date.now();
  if (limit) {
      // simple limit
      for (let i = 0; i < chunks.length; i += limit) {
          const batch = chunks.slice(i, i + limit);
          await Promise.all(batch.map(chunk => mockSendMessage('chatId', chunk)));
      }
  } else {
      await Promise.all(chunks.map(chunk => mockSendMessage('chatId', chunk)));
  }
  return Date.now() - start;
}

async function main() {
  const chunks = Array.from({length: 20}, (_, i) => `chunk ${i}`);

  console.log("Running sequential...");
  const seqTime = await runSequential(chunks);

  console.log("Running concurrent (limit 5)...");
  const conTimeLimited = await runConcurrent(chunks, 5);

  console.log("Running concurrent (no limit)...");
  const conTime = await runConcurrent(chunks);

  console.log(`Sequential: ${seqTime}ms`);
  console.log(`Concurrent (limit 5): ${conTimeLimited}ms`);
  console.log(`Concurrent (no limit): ${conTime}ms`);
}

main();

import { performance } from "perf_hooks";

// Mocking function to simulate the `sendBlueBubblesMedia`
const sendBlueBubblesMedia = async (args: any) => {
    return new Promise((resolve) => setTimeout(() => resolve({ messageId: "123" }), 50));
};

const mediaList = Array.from({ length: 5 }, (_, i) => `http://example.com/media${i}.jpg`);

const seqBench = async () => {
    const start = performance.now();
    for (const mediaUrl of mediaList) {
        await sendBlueBubblesMedia({ mediaUrl });
    }
    const end = performance.now();
    return end - start;
};

const parBench = async () => {
    const start = performance.now();
    await Promise.all(mediaList.map(async (mediaUrl) => {
        await sendBlueBubblesMedia({ mediaUrl });
    }));
    const end = performance.now();
    return end - start;
};

const run = async () => {
    console.log(`Sequential: ${await seqBench()} ms`);
    console.log(`Parallel: ${await parBench()} ms`);
};

run();

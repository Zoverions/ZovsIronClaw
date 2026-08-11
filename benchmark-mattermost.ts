import { performance } from 'node:perf_hooks';

const SLEEP_MS = 100;
async function sendMessageMattermostMock(mediaUrl: string, caption: string) {
    await new Promise(resolve => setTimeout(resolve, SLEEP_MS));
    return true;
}

async function runTest(mediaUrls: string[], text: string) {
    const start = performance.now();
    let first = true;
    for (const mediaUrl of mediaUrls) {
        const caption = first ? text : "";
        first = false;
        await sendMessageMattermostMock(mediaUrl, caption);
    }
    const end = performance.now();
    return end - start;
}

async function runOptimizedTest(mediaUrls: string[], text: string) {
    const start = performance.now();
    await Promise.all(
        mediaUrls.map((mediaUrl, index) => {
            const caption = index === 0 ? text : "";
            return sendMessageMattermostMock(mediaUrl, caption);
        })
    );
    const end = performance.now();
    return end - start;
}


async function main() {
    const urls = Array.from({length: 10}, (_, i) => `url${i}`);
    const time1 = await runTest(urls, "text");
    const time2 = await runOptimizedTest(urls, "text");
    console.log(`Baseline: ${time1} ms`);
    console.log(`Optimized: ${time2} ms`);
}

main();

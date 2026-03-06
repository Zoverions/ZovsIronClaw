import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { performance } from "node:perf_hooks";

async function runBenchmark() {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "bench-"));
  const extraPaths = [];
  for (let i = 0; i < 2000; i++) {
    const p = path.join(dir, `dummy-${i}.txt`);
    await fs.writeFile(p, "dummy content");
    extraPaths.push(p);
  }

  const checkReadableFile = async (pathname: string) => {
    try {
      await fs.access(pathname, 4); // R_OK
      return { exists: true };
    } catch (err) {
      return { exists: false, issue: "error" };
    }
  };

  const issues = [];
  const startSeq = performance.now();
  for (const extraPath of extraPaths) {
    try {
      const stat = await fs.lstat(extraPath);
      if (stat.isSymbolicLink()) {
        continue;
      }
      const extraCheck = await checkReadableFile(extraPath);
      if (extraCheck.issue) {
        issues.push(extraCheck.issue);
      }
    } catch (err) {
      issues.push("error");
    }
  }
  const endSeq = performance.now();
  console.log(`Sequential: ${endSeq - startSeq} ms`);

  const issues2 = [];
  const startPar = performance.now();
  const extraIssues = await Promise.all(
    extraPaths.map(async (extraPath) => {
      try {
        const stat = await fs.lstat(extraPath);
        if (stat.isSymbolicLink()) {
          return null;
        }
        const extraCheck = await checkReadableFile(extraPath);
        if (extraCheck.issue) {
          return extraCheck.issue;
        }
      } catch (err) {
        return "error";
      }
      return null;
    })
  );
  for (const issue of extraIssues) {
    if (issue) issues2.push(issue);
  }
  const endPar = performance.now();
  console.log(`Parallel: ${endPar - startPar} ms`);

  await fs.rm(dir, { recursive: true, force: true });
}

runBenchmark().catch(console.error);

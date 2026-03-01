export function findFirstMatch<T, U>(
  candidates: (T | undefined | null)[],
  mapper: (item: T) => U | undefined | null,
): U | undefined {
  for (const candidate of candidates) {
    if (candidate === undefined || candidate === null) {
      continue;
    }
    const result = mapper(candidate);
    if (result) {
      return result;
    }
  }
  return undefined;
}

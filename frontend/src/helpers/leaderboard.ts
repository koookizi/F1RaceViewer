export function atOrBefore<T extends { SessionTime: number }>(
  rows: T[],
  currentTime: number
): T | null {
  if (!rows.length) return null;
  if (currentTime < rows[0].SessionTime) return null;

  let lo = 0,
    hi = rows.length - 1,
    ans = -1;

  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (rows[mid].SessionTime <= currentTime) {
      ans = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }

  return ans >= 0 ? rows[ans] : null;
}

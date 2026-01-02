export const getMax = (rows: any[], key: string, fallback: number) => {
  if (!rows?.length) return fallback;
  const max = Math.max(...rows.map((r) => Number(r?.[key] ?? 0)));
  return max > 0 ? max : fallback;
};

export type TelemetryRow = {
  SessionTime: number;
  [key: string]: any;
};

function clamp01(x: number) {
  return Math.max(0, Math.min(1, x));
}

export function getInterpolatedValue<T extends TelemetryRow>(
  rows: T[],
  key: keyof T,
  t: number
): number | null {
  if (!rows?.length) return null;

  // clamp to ends
  if (t <= rows[0].SessionTime) return Number(rows[0][key] ?? 0);
  if (t >= rows[rows.length - 1].SessionTime)
    return Number(rows[rows.length - 1][key] ?? 0);

  // binary search for rightmost row with SessionTime <= t
  let lo = 0;
  let hi = rows.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const tm = rows[mid].SessionTime;
    if (tm <= t) lo = mid + 1;
    else hi = mid - 1;
  }

  const i0 = Math.max(0, hi);
  const i1 = Math.min(rows.length - 1, i0 + 1);

  const a = rows[i0];
  const b = rows[i1];

  const t0 = a.SessionTime;
  const t1 = b.SessionTime;
  const v0 = Number(a[key] ?? 0);
  const v1 = Number(b[key] ?? 0);

  const alpha = t1 === t0 ? 0 : clamp01((t - t0) / (t1 - t0));
  return v0 + (v1 - v0) * alpha;
}

// For discrete states like DRS: pick last-known value at/before time t
export function getStepValue<T extends TelemetryRow>(
  rows: T[],
  key: keyof T,
  t: number
): number | null {
  if (!rows?.length) return null;

  if (t <= rows[0].SessionTime) return Number(rows[0][key] ?? 0);
  if (t >= rows[rows.length - 1].SessionTime)
    return Number(rows[rows.length - 1][key] ?? 0);

  let lo = 0;
  let hi = rows.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const tm = rows[mid].SessionTime;
    if (tm <= t) lo = mid + 1;
    else hi = mid - 1;
  }

  return Number(rows[Math.max(0, hi)][key] ?? 0);
}

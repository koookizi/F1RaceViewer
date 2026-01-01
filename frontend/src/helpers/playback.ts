export function getPositionAtTime(samples: any[], t: number) {
  if (!samples.length) return null;
  if (t <= samples[0].t) return samples[0];
  if (t >= samples[samples.length - 1].t) return samples[samples.length - 1];

  for (let i = 0; i < samples.length - 1; i++) {
    const a = samples[i];
    const b = samples[i + 1];
    if (t >= a.t && t <= b.t) {
      const ratio = (t - a.t) / (b.t - a.t || 1);
      return {
        t,
        lap: a.lap,
        x: a.x + (b.x - a.x) * ratio,
        y: a.y + (b.y - a.y) * ratio,
      };
    }
  }
  return samples[samples.length - 1];
}

export function formatWallClockTime(
  sessionStart: string | Date | null,
  sessionTimeSeconds: number | null
): string {
  if (!sessionStart || sessionTimeSeconds == null) return "--:--:--";

  const start =
    typeof sessionStart === "string" ? new Date(sessionStart) : sessionStart;

  if (isNaN(start.getTime())) return "--:--:--";

  // Add SessionTime (seconds) to t0 (UTC instant)
  const wallTime = new Date(start.getTime() + sessionTimeSeconds * 1000);

  const hh = wallTime.getUTCHours().toString().padStart(2, "0");
  const mm = wallTime.getUTCMinutes().toString().padStart(2, "0");
  const ss = wallTime.getUTCSeconds().toString().padStart(2, "0");

  return `${hh}:${mm}:${ss}`;
}

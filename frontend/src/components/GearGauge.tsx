import { useMemo } from "react";
import GaugeComponent from "react-gauge-component";
import type { LeaderboardCarData } from "../types";
import { getStepValue } from "../helpers/gauge";

type GearGaugeProps = {
  carData: LeaderboardCarData[];
  currentTime: number;
  size?: number;
  /** Max number of forward gears (F1 is typically 8) */
  maxGears?: number;
};

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

/**
 * Linear gradient between 3 colors: red -> green -> blue.
 * i in [1..maxGears]
 */
function gearColor(i: number, maxGears: number) {
  // anchors
  const c1 = { r: 239, g: 68, b: 68 }; // red-500
  const c2 = { r: 34, g: 197, b: 94 }; // green-500
  const c3 = { r: 59, g: 130, b: 246 }; // blue-500

  if (maxGears <= 1) return `rgb(${c3.r},${c3.g},${c3.b})`;

  const t = (i - 1) / (maxGears - 1); // 0..1

  // first half: red->green, second half: green->blue
  if (t <= 0.5) {
    const u = t / 0.5; // 0..1
    const r = Math.round(c1.r + (c2.r - c1.r) * u);
    const g = Math.round(c1.g + (c2.g - c1.g) * u);
    const b = Math.round(c1.b + (c2.b - c1.b) * u);
    return `rgb(${r},${g},${b})`;
  } else {
    const u = (t - 0.5) / 0.5; // 0..1
    const r = Math.round(c2.r + (c3.r - c2.r) * u);
    const g = Math.round(c2.g + (c3.g - c2.g) * u);
    const b = Math.round(c2.b + (c3.b - c2.b) * u);
    return `rgb(${r},${g},${b})`;
  }
}

export function GearGauge({
  carData,
  currentTime,
  size = 160,
  maxGears = 8,
}: GearGaugeProps) {
  const rows = useMemo(() => {
    const arr = (carData ?? []).slice();
    arr.sort((a: any, b: any) => (a.SessionTime ?? 0) - (b.SessionTime ?? 0));
    return arr;
  }, [carData]);

  // Gear key can differ depending on source:
  // FastF1 often uses "nGear"; your earlier screenshot showed "Gear".
  const gearRaw =
    getStepValue(rows as any, "nGear" as any, currentTime) ??
    getStepValue(rows as any, "Gear" as any, currentTime) ??
    0;

  // Handle neutral / reverse nicely
  // - If your data uses 0 for N, display "N"
  // - If your data uses -1 for R, display "R"
  const gearNum = Number(gearRaw ?? 0);

  const displayText =
    gearNum < 0
      ? "R"
      : gearNum === 0
      ? "N"
      : String(clamp(gearNum, 1, maxGears));

  // Gauge value: keep within [0..maxGears]
  // If in N or R, park at 0 so needle sits at start
  const gaugeValue = gearNum >= 1 ? clamp(gearNum, 1, maxGears) : 0;

  // Build exactly X equal segments, with colors red->green->blue
  const colorArray = useMemo(() => {
    return Array.from({ length: maxGears }, (_, idx) =>
      gearColor(idx + 1, maxGears)
    );
  }, [maxGears]);

  const subArcs = useMemo(() => {
    // limits at 1,2,3,... (last segment has no limit)
    return Array.from({ length: maxGears }, (_, idx) => {
      const gear = idx + 1;
      return gear < maxGears ? { limit: gear } : {};
    });
  }, [maxGears]);

  return (
    <div className="relative -ms-4 -mt-4" style={{ width: size, height: size }}>
      {/* GAUGE LAYER */}
      <div style={{ width: "100%", height: "100%" }}>
        <GaugeComponent
          type="radial"
          value={gaugeValue}
          minValue={0}
          maxValue={maxGears}
          style={{ width: "100%", height: "100%" }}
          labels={{
            valueLabel: { hide: true },
            tickLabels: { hideMinMax: true, type: "inner", ticks: [] },
          }}
          arc={{
            colorArray,
            subArcs,
            padding: 0,
            width: 0.26,
          }}
          pointer={{
            elastic: false,
            animationDelay: 0,
            animationDuration: 140,
          }}
        />
      </div>

      {/* TEXT LAYER */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute left-1/2 -translate-x-1/2 text-center"
          style={{ bottom: size * 0.18 }}
        >
          <div className="text-2xl leading-none font-semibold tabular-nums">
            {displayText}
          </div>
          <div className="text-[11px] opacity-70 tracking-wider">GEAR</div>
        </div>
      </div>
    </div>
  );
}

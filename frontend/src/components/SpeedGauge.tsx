import { useMemo } from "react";
import GaugeComponent from "react-gauge-component";
import type { LeaderboardCarData } from "../types";
import { getInterpolatedValue, getStepValue } from "../helpers/gauge";

const MAX_SPEED = 360;

type DrsState = "off" | "available" | "active";

function classifyDrs(v: number | null | undefined): DrsState {
  const n = Number(v ?? 0);

  if (n === 8) return "available"; 
  if (n === 10 || n === 12 || n === 14) return "active";
  return "off";
}

/**
 * Displays vehicle speed using a gauge-style visualisation.
 *
 * Updated continuously during playback to reflect live telemetry data.
 */
export function SpeedGauge({
  carData,
  currentTime,
  size = 160,
}: {
  carData: LeaderboardCarData[];
  currentTime: number;
  size?: number;
}) {
  const rows = useMemo(() => {
    const arr = (carData ?? []).slice();
    arr.sort((a: any, b: any) => (a.SessionTime ?? 0) - (b.SessionTime ?? 0));
    return arr;
  }, [carData]);

  const rawSpeed =
    getInterpolatedValue(rows as any, "Speed" as any, currentTime) ?? 0;
  const speed = Math.max(0, Math.min(rawSpeed, MAX_SPEED));

  const drsValue = getStepValue(rows as any, "DRS" as any, currentTime);
  const drsState = classifyDrs(drsValue);

  const gaugeGlowClass =
    drsState === "active"
      ? "drop-shadow-[0_0_10px_rgba(34,211,238,0.95)] drop-shadow-[0_0_18px_rgba(34,211,238,0.85)]"
      : drsState === "available"
      ? "drop-shadow-[0_0_8px_rgba(148,163,184,0.9)] drop-shadow-[0_0_14px_rgba(148,163,184,0.75)]"
      : "";

  return (
    <div className="relative -ms-4 -mt-4" style={{ width: size, height: size }}>
      {/* Gauge layer (glow applies here only) */}
      <div className={gaugeGlowClass} style={{ width: "100%", height: "100%" }}>
        <GaugeComponent
          type="radial"
          value={speed}
          minValue={0}
          maxValue={MAX_SPEED}
          style={{ width: "100%", height: "100%" }}
          labels={{
            valueLabel: { hide: true },
            tickLabels: { hideMinMax: true, type: "inner", ticks: [] }, // no tick text/segments
          }}
          arc={{
            colorArray: ["#5BE12C", "#F5CD19", "#EA4228"],
            subArcs: [{ limit: 180 }, { limit: 260 }, { limit: 320 }, {}],
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

      {/* Text layer (no glow, lower middle) */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute left-1/2 -translate-x-1/2 text-center"
          style={{ bottom: size * 0.18 }}
        >
          <div className="text-2xl leading-none font-semibold tabular-nums">
            {Math.round(speed)}
          </div>
          <div className="text-[11px] opacity-70 tracking-wider">KM/H</div>

          {/* DRS label */}
          {drsState !== "off" && (
            <div
              className={[
                "mt-1 text-[10px] font-semibold tracking-wider",
                drsState === "active" ? "text-cyan-300" : "text-slate-300",
              ].join(" ")}
            >
              DRS
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

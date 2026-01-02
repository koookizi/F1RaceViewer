import { useMemo } from "react";
import GaugeComponent from "react-gauge-component";
import type { LeaderboardCarData } from "../types";
import { getInterpolatedValue } from "../helpers/gauge";

const MAX_RPM = 12_000;

export function RpmGauge({
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

  const rawRpm =
    getInterpolatedValue(rows as any, "RPM" as any, currentTime) ?? 0;
  const rpm = Math.max(0, Math.min(rawRpm, MAX_RPM));

  const frac = rpm / MAX_RPM;
  const nearLimiter = frac >= 0.92;
  const onLimiter = frac >= 0.97;

  return (
    <div className="relative -ms-5 -mt-4" style={{ width: size, height: size }}>
      {/* GAUGE LAYER (glow applies here only) */}
      <div
        className={[
          nearLimiter ? "drop-shadow-[0_0_14px_rgba(239,68,68,0.55)]" : "",
          onLimiter ? "animate-pulse" : "",
        ].join(" ")}
        style={{ width: "100%", height: "100%" }}
      >
        <GaugeComponent
          type="radial"
          value={rpm}
          minValue={0}
          maxValue={MAX_RPM}
          style={{ width: "100%", height: "100%" }}
          labels={{
            valueLabel: { hide: true },
            tickLabels: { hideMinMax: true, type: "inner", ticks: [] }, // remove tick text/segments
          }}
          arc={{
            colorArray: ["#5BE12C", "#F5CD19", "#EA4228"],
            subArcs: [{ limit: 7000 }, { limit: 9500 }, { limit: 11000 }, {}],
            padding: 0, // remove padding between arc segments
            width: 0.26,
          }}
          pointer={{
            elastic: false,
            animationDelay: 0,
            animationDuration: 160,
          }}
        />
      </div>

      {/* TEXT LAYER (no glow, lower middle) */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute left-1/2 -translate-x-1/2 text-center"
          style={{ bottom: size * 0.18 }}
        >
          <div
            className={[
              "text-1xl leading-none font-semibold tabular-nums",
              nearLimiter ? "text-red-300" : "",
            ].join(" ")}
          >
            {Math.round(rpm)}
          </div>
          <div className="text-[11px] opacity-70 tracking-wider">RPM</div>
        </div>
      </div>
    </div>
  );
}

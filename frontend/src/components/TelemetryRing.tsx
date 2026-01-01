import React, { useEffect, useMemo, useState } from "react";
import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import { useMotionValue, useSpring, useMotionValueEvent } from "framer-motion";

import "react-circular-progressbar/dist/styles.css";

type TelemetryRingProps = {
  /** 0..100 */
  percent: number;
  /** text shown big in the center (you can pass "1.5" or "66") */
  valueText: string;
  /** small label like TRC/AIR */
  label: string;
  /** ring color */
  color: string;

  /** visual tuning */
  size?: number; // px
  strokeWidth?: number; // progress thickness
  gapRatio?: number; // 0.75..0.9 (how much of the circle is drawn)
};

export function TelemetryRing({
  percent,
  valueText,
  label,
  color,
  size = 54,
  strokeWidth = 10,
  gapRatio = 0.82,
}: TelemetryRingProps) {
  const clamped = Math.max(0, Math.min(100, percent ?? 0));

  const mv = useMotionValue(clamped);
  const spring = useSpring(mv, { stiffness: 140, damping: 22 });

  const [animated, setAnimated] = React.useState(clamped);

  // drive mv from props
  React.useEffect(() => {
    mv.set(clamped);
  }, [clamped, mv]);

  // throttle setState to once per frame + avoid redundant sets
  const rafRef = React.useRef<number | null>(null);
  const latestRef = React.useRef<number>(clamped);
  const lastCommittedRef = React.useRef<number>(clamped);

  useMotionValueEvent(spring, "change", (v) => {
    latestRef.current = v;

    if (rafRef.current != null) return;
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;

      // round to reduce churn; change 1 => integer %, 0.1 => tenth precision
      const next = Math.round(latestRef.current * 10) / 10;

      if (next !== lastCommittedRef.current) {
        lastCommittedRef.current = next;
        setAnimated(next);
      }
    });
  });

  React.useEffect(() => {
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  // Where the arc starts (rotation). This positions the gap at the bottom.
  // CircularProgressbar rotation is in turns (1 = full circle).
  const rotation = 1 - gapRatio / 2; // centers the gap at bottom

  // Little cap dot at the start of the arc (like your screenshot)
  const dot = useMemo(() => {
    const r = 0.5; // relative radius inside 100x100 box
    const strokeInset = 0.08; // keep dot aligned with stroke visually
    const radius = 50 - strokeWidth + strokeInset * 100;

    // Start angle (in degrees) for the arc:
    // -90° is top. rotation shifts it.
    const startAngleDeg = -90 + rotation * 360;
    const rad = (startAngleDeg * Math.PI) / 180;

    const cx = 50 + radius * Math.cos(rad);
    const cy = 50 + radius * Math.sin(rad);

    return { cx, cy };
  }, [rotation, strokeWidth]);

  return (
    <div
      className="relative grid place-items-center"
      style={{ width: size, height: size }}
    >
      <CircularProgressbar
        value={animated}
        maxValue={100}
        circleRatio={gapRatio}
        styles={buildStyles({
          rotation,
          pathColor: color,
          trailColor: "rgb(31 41 55)", // gray-800-ish
          strokeLinecap: "round",
          pathTransition: "none", // we animate via framer spring
        })}
        strokeWidth={strokeWidth}
      />

      {/* start cap dot */}
      <svg className="absolute inset-0" viewBox="0 0 100 100">
        <circle cx={dot.cx} cy={dot.cy} r="3.2" fill={color} />
      </svg>

      {/* center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <div className="text-white font-extrabold text-lg">{valueText}</div>
        <div className="text-white/80 text-[10px] font-semibold tracking-wide">
          {label}
        </div>
      </div>
    </div>
  );
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

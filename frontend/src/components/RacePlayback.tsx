// src/components/RacePlayback.tsx
import React from "react";
import type { PlaybackData } from "../types";
import { getPositionAtTime } from "../helpers/playback";

type RacePlaybackProps = {
  data: PlaybackData | null;
  currentTime: number;
};

export function RacePlayback({ data, currentTime }: RacePlaybackProps) {
  if (!data) {
    return <div className="skeleton h-32 w-auto mt-5"></div>;
  }

  const { track, drivers } = data;

  return (
    <div className="w-full flex justify-center mt-5">
      <svg
        viewBox="-1.2 -1.2 2.4 2.4"
        className="w-full max-w-3xl border rounded-xl bg-neutral-900"
      >
        {/* track polyline */}
        <polyline
          fill="none"
          stroke="#555"
          strokeWidth={0.01}
          points={track.points.map(([x, y]) => `${x},${-y}`).join(" ")}
        />

        {/* driver dots */}
        {drivers.map((drv) => {
          const pos = getPositionAtTime(drv.samples, currentTime);
          if (!pos) return null;
          return (
            <circle
              key={drv.code}
              cx={pos.x}
              cy={-pos.y}
              r={0.02}
              fill={drv.color || "white"}
            >
              <title>{drv.code}</title>
            </circle>
          );
        })}
      </svg>
    </div>
  );
}

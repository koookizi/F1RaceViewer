// src/components/RacePlayback.tsx
import React from "react";
import type { PlaybackData, LeaderboardApiResponse } from "../types";
import { getPositionAtTime } from "../helpers/playback";
import { teamBgByDriver } from "../helpers/team_colour";

type RacePlaybackCircuitProps = {
  data: PlaybackData | null;
  leaderboardData: LeaderboardApiResponse | null;
  currentTime: number;
};

export function RacePlaybackCircuit({
  data,
  currentTime,
  leaderboardData,
}: RacePlaybackCircuitProps) {
  if (!data) {
    return <div className="skeleton h-32 w-auto"></div>;
  }

  const { track, drivers } = data;

  return (
    <div className="w-full flex justify-center">
      <svg viewBox="-1.2 -1.2 2.4 2.4" className="w-full max-w-3xl">
        {/* track polyline */}
        <polyline
          fill="none"
          stroke="#05070eff"
          strokeWidth={0.05}
          points={track.points.map(([x, y]) => `${x},${-y}`).join(" ")}
        />

        <polyline
          fill="none"
          stroke="#dadadaff"
          strokeWidth={0.01}
          points={track.points.map(([x, y]) => `${x},${-y}`).join(" ")}
        />

        {/* driver dots */}
        {drivers.map((drv) => {
          const pos = getPositionAtTime(drv.samples, currentTime);
          if (!pos) return null;

          const r = 0.02;
          const labelOffset = 0.035; // distance to the right of the dot

          return (
            <g key={drv.code}>
              {/* dot */}
              <circle
                cx={pos.x}
                cy={-pos.y}
                r={r}
                fill={teamBgByDriver(leaderboardData, drv.code, "opaque")}
              />

              {/* text label */}
              <text
                x={pos.x + labelOffset}
                y={-pos.y}
                fill={teamBgByDriver(leaderboardData, drv.code, "opaque")}
                fontSize={0.06}
                fontWeight={600}
                dominantBaseline="middle"
                textAnchor="start"
                pointerEvents="none"
                style={{ userSelect: "none" }}
              >
                {drv.code}
              </text>

              <title>{drv.code}</title>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

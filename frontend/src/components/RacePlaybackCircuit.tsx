// src/components/RacePlayback.tsx
import React from "react";
import type { PlaybackData, LeaderboardApiResponse } from "../types";
import { getPositionAtTime } from "../helpers/playback";
import { teamBgByDriver } from "../helpers/team_colour";
import { getDriverNumberByAbbreviation } from "../helpers/driver_identifiers";

type RacePlaybackCircuitProps = {
  data: PlaybackData | null;
  leaderboardData: LeaderboardApiResponse | null;
  currentTime: number;
  selectedDriver: number | null;
};

export function RacePlaybackCircuit({
  data,
  currentTime,
  leaderboardData,
  selectedDriver,
}: RacePlaybackCircuitProps) {
  if (!data) {
    return <div className="skeleton h-32 w-auto"></div>;
  }

  const { track, drivers } = data;

  return (
    <div className="w-full flex justify-center">
      <svg viewBox="-1.2 -1.2 2.4 2.4" className="w-full max-w-3xl">
        {/* ===== GLOW FILTER (isolated per element) ===== */}
        <defs>
          <filter
            id="driverGlow"
            filterUnits="objectBoundingBox"
            x={-0.8}
            y={-0.8}
            width={2.6}
            height={2.6}
          >
            <feGaussianBlur
              in="SourceGraphic"
              stdDeviation={0.03}
              result="blur"
            />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* ===== TRACK ===== */}
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

        {/* ===== DRIVERS ===== */}
        {drivers.map((drv) => {
          const pos = getPositionAtTime(drv.samples, currentTime);
          if (!pos) return null;

          const r = 0.02;
          const labelOffset = 0.035;

          const driverNumber = getDriverNumberByAbbreviation(
            leaderboardData,
            drv.code
          );

          // 🔴 CORRECT selection logic (by driver number)
          const isSelected =
            selectedDriver != null && driverNumber === selectedDriver;

          const dimOthers = selectedDriver != null && !isSelected;

          const teamColor = teamBgByDriver(leaderboardData, drv.code, "opaque");

          return (
            <g key={drv.code} opacity={dimOthers ? 0.5 : 1}>
              {/* dot */}
              <circle
                cx={pos.x}
                cy={-pos.y}
                r={isSelected ? r * 1.25 : r}
                fill={teamColor}
                filter={isSelected ? "url(#driverGlow)" : undefined}
              />

              {/* label */}
              <text
                x={pos.x + labelOffset}
                y={-pos.y}
                fill={teamColor}
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

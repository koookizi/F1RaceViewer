import React from "react";
import type { LeaderboardLapsData, LeaderboardDriverData } from "../types";
import { atOrBefore } from "../helpers/leaderboard";

/** F1 universal-ish colours you asked to keep */
const LAP_PURPLE = "#A855F7"; // session best / purple
const LAP_GREEN = "#22C55E"; // personal best / green
const LAP_NEUTRAL = "#E5E7EB"; // normal light
const LAP_DIM = "#9CA3AF"; // dim/no data

/** Extra colours used for OpenF1 minisector codes */
const MINI_YELLOW = "#FACC15"; // yellow minisector
const MINI_PIT = "#60A5FA"; // pitlane minisector (blue-ish)
const MINI_PENDING = "#374151"; // dark pending

function pickSectorTime(lap: LeaderboardLapsData, sector: 1 | 2 | 3): number {
  return sector === 1
    ? lap.duration_sector_1
    : sector === 2
    ? lap.duration_sector_2
    : lap.duration_sector_3;
}

function pickSectorSegments(
  lap: LeaderboardLapsData,
  sector: 1 | 2 | 3
): number[] {
  const segs =
    sector === 1
      ? lap.segments_sector_1
      : sector === 2
      ? lap.segments_sector_2
      : lap.segments_sector_3;

  return Array.isArray(segs) ? segs : [];
}

/** Sector times in OpenF1 are seconds; your screenshot format is SS.mmm */
function formatSectorTime(seconds: number | null): string {
  if (seconds == null || seconds <= 0) return "—";
  const totalMs = Math.round(seconds * 1000);
  const s = Math.floor(totalMs / 1000);
  const ms = totalMs - s * 1000;
  return `${s}.${ms.toString().padStart(3, "0")}`;
}

/** Driver best sector time so far (up to currentTime) */
function getDriverBestSectorTimeSoFar(
  laps: LeaderboardLapsData[],
  sector: 1 | 2 | 3,
  currentTime: number
): number | null {
  let best = Infinity;
  for (const l of laps) {
    if (l.SessionTime > currentTime) continue;
    if (l.is_pit_out_lap) continue;
    const v = pickSectorTime(l, sector);
    if (v > 0 && v < best) best = v;
  }
  return best === Infinity ? null : best;
}

/** Session best sector time so far (up to currentTime), across all drivers */
function getSessionBestSectorTimeSoFar(
  drivers: LeaderboardDriverData[],
  sector: 1 | 2 | 3,
  currentTime: number
): number | null {
  let best = Infinity;
  for (const d of drivers) {
    for (const l of d.laps_data) {
      if (l.SessionTime > currentTime) continue;
      if (l.is_pit_out_lap) continue;
      const v = pickSectorTime(l, sector);
      if (v > 0 && v < best) best = v;
    }
  }
  return best === Infinity ? null : best;
}

/**
 * F1-style colour for the displayed sector time:
 * purple if session best so far, green if driver PB so far, else neutral/dim.
 */
function getSectorTimeColorHex(
  displayedSeconds: number | null,
  driver: LeaderboardDriverData,
  allDrivers: LeaderboardDriverData[],
  sector: 1 | 2 | 3,
  currentTime: number
): string {
  if (displayedSeconds == null || displayedSeconds <= 0) return LAP_DIM;

  const displayedMs = Math.round(displayedSeconds * 1000);

  const driverBest = getDriverBestSectorTimeSoFar(
    driver.laps_data,
    sector,
    currentTime
  );
  const sessionBest = getSessionBestSectorTimeSoFar(
    allDrivers,
    sector,
    currentTime
  );

  if (driverBest == null || sessionBest == null) return LAP_NEUTRAL;

  const driverBestMs = Math.round(driverBest * 1000);
  const sessionBestMs = Math.round(sessionBest * 1000);

  if (displayedMs === sessionBestMs) return LAP_PURPLE;
  if (displayedMs === driverBestMs) return LAP_GREEN;
  return LAP_NEUTRAL;
}

/**
 * OpenF1 minisector codes mapping (per docs):
 * 0 not available, 2048 yellow, 2049 green, 2051 purple, 2064 pitlane. :contentReference[oaicite:1]{index=1}
 */
function minisectorCodeToHex(code: number | null | undefined): string {
  if (code == null) return MINI_PENDING;
  switch (code) {
    case 0:
      return MINI_PENDING; // not available
    case 2048:
      return MINI_YELLOW;
    case 2049:
      return LAP_GREEN;
    case 2051:
      return LAP_PURPLE;
    case 2064:
      return MINI_PIT;
    default:
      // unknown codes exist per docs; keep them dim so UI doesn't lie
      return LAP_DIM;
  }
}

type SectorWidgetProps = {
  driver: LeaderboardDriverData;
  allDrivers: LeaderboardDriverData[]; // needed for session-best purple
  currentTime: number;
  sector: 1 | 2 | 3;

  /** Optional: force a specific number of blocks (pad/trim) */
  blockCount?: number;

  /** Styling knobs */
  widthPx?: number;
  blockWidthPx?: number;
  blockHeightPx?: number;
  blockGapPx?: number;

  /** Make the small reference time slightly transparent */
  referenceOpacity?: number;
};

export function SectorWidget({
  driver,
  allDrivers,
  currentTime,
  sector,
  blockCount,
  widthPx = 140,
  blockWidthPx = 10,
  blockHeightPx = 6,
  blockGapPx = 3,
  referenceOpacity = 0.75,
}: SectorWidgetProps) {
  const laps = driver?.laps_data ?? [];
  const lap = atOrBefore(laps, currentTime);

  const currentSector = lap ? pickSectorTime(lap, sector) : null;
  const refSector = getDriverBestSectorTimeSoFar(
    driver.laps_data,
    sector,
    currentTime
  );

  const timeColor = getSectorTimeColorHex(
    currentSector,
    driver,
    allDrivers,
    sector,
    currentTime
  );

  const segmentsRaw = lap ? pickSectorSegments(lap, sector) : [];
  const segmentsSafe = Array.isArray(segmentsRaw) ? segmentsRaw : [];

  return (
    <div className="flex flex-col gap-1" style={{ width: widthPx }}>
      {/* minisectors */}
      <div
        className="flex items-center"
        style={{ gap: blockGapPx, height: blockHeightPx }}
      >
        {segmentsSafe.map((code, i) => (
          <span
            key={i}
            className="inline-block"
            style={{
              width: blockWidthPx,
              height: blockHeightPx,
              borderRadius: 1,
              backgroundColor: minisectorCodeToHex(code),
              opacity: code === 0 || code == null ? 0.55 : 1,
            }}
          />
        ))}
      </div>

      {/* time text like F1-dash */}
      <div className="inline-flex items-baseline gap-2 leading-none">
        <span
          className="font-mono font-semibold tabular-nums"
          style={{
            color: timeColor,
            fontSize: 22,
            letterSpacing: 0.2,
          }}
        >
          {formatSectorTime(currentSector)}
        </span>

        <span
          className="font-mono tabular-nums"
          style={{
            color: LAP_DIM,
            fontSize: 14,
            letterSpacing: 0.2,
            opacity: referenceOpacity,
            transform: "translateY(-1px)",
          }}
        >
          {formatSectorTime(refSector)}
        </span>
      </div>
    </div>
  );
}

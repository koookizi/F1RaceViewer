import React, { useEffect, useState } from "react";
import type {
  LeaderboardApiResponse,
  LeaderboardPositionsData,
  LeaderboardLapsData,
  LeaderboardStintData,
  LeaderboardPitData,
  Compound,
  LeaderboardCarData,
  LeaderboardGapData,
  LeaderboardDriverData,
} from "../types";
import { motion, AnimatePresence } from "framer-motion";
import hardTyre from "../assets/hard.svg";
import intermediateTyre from "../assets/intermediate.svg";
import mediumTyre from "../assets/medium.svg";
import softTyre from "../assets/soft.svg";
import unknownTyre from "../assets/unknown.svg";
import wetTyre from "../assets/wet.svg";
import { atOrBefore } from "../helpers/leaderboard";
import { SectorWidget } from "../components/SectorWidget";

type RacePlaybackLeaderboardProps = {
  leaderboardData: LeaderboardApiResponse | null;
  currentTime: number;
};

export function RacePlaybackLeaderboard({
  leaderboardData,
  currentTime,
}: RacePlaybackLeaderboardProps) {
  if (!leaderboardData) {
    return <div className="skeleton h-32 w-auto"></div>;
  }
  return (
    <div className="card card-border bg-base-100">
      <div className="card-body">
        <div className="w-full overflow-x-auto overflow-anchor-none">
          <table className="table [&_td]:py-1 min-w-max">
            <thead></thead>
            <tbody>
              <AnimatePresence initial={false}>
                {leaderboardData?.drivers
                  .slice()
                  .sort(
                    (a, b) =>
                      (getPos(a.positions_data, currentTime) ?? 9999) -
                      (getPos(b.positions_data, currentTime) ?? 9999)
                  )
                  .map((driver) => (
                    <motion.tr
                      key={driver.driver_code}
                      layout // <- this is what animates the movement
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      transition={{
                        type: "spring",
                        stiffness: 300,
                        damping: 30,
                      }}
                    >
                      <td>
                        <div
                          className="badge font-bold flex py-4 w-23 ps-6 "
                          style={{
                            backgroundColor: `#${driver.team_colour}`,
                            color: `color-mix(in srgb, #${driver.team_colour} 20%, black)`,
                            filter: "brightness(0.8)",
                            border: 0,
                          }}
                        >
                          {getPos(driver.positions_data, currentTime)}
                          <div
                            className="badge font-bold"
                            style={{
                              backgroundColor: "white",
                              color: `#${driver.team_colour}`,
                              border: 0,
                            }}
                          >
                            {driver.driver_code}
                          </div>
                        </div>
                      </td>
                      <td>
                        {(() => {
                          switch (
                            getDRSPITStatus(
                              driver.pit_data,
                              driver.car_data,
                              currentTime
                            )
                          ) {
                            case "Off":
                              return (
                                <div className="badge border-2 font-bold bg-transparent text-[#3f3f46] border-[#3f3f46] h-8">
                                  DRS
                                </div>
                              );

                            case "Possible":
                              return (
                                <div className="badge border-2 font-bold bg-transparent text-[#9f9fa8] border-[#9f9fa8] h-8">
                                  DRS
                                </div>
                              );

                            case "Active":
                              return (
                                <div className="badge border-2 font-bold bg-transparent text-[#5ab982] border-[#5ab982] h-8">
                                  DRS
                                </div>
                              );

                            case "Pit":
                              return (
                                <div className="badge border-2 font-bold bg-transparent text-[#5eb5d6] border-[#5eb5d6] h-8">
                                  PIT
                                </div>
                              );

                            default:
                              return null;
                          }
                        })()}
                      </td>
                      <td>
                        <div className="flex items-center">
                          <div>
                            {(() => {
                              switch (
                                getCompound(
                                  driver.pit_data,
                                  driver.stint_data,
                                  currentTime
                                )
                              ) {
                                case "UNKNOWN":
                                  return (
                                    <img src={unknownTyre} className="h-8" />
                                  );

                                case "WET":
                                  return <img src={wetTyre} className="h-8" />;

                                case "SOFT":
                                  return <img src={softTyre} className="h-8" />;

                                case "MEDIUM":
                                  return (
                                    <img src={mediumTyre} className="h-8" />
                                  );

                                case "INTERMEDIATE":
                                  return (
                                    <img
                                      src={intermediateTyre}
                                      className="h-8"
                                    />
                                  );

                                case "HARD":
                                  return <img src={hardTyre} className="h-8" />;

                                default:
                                  return null;
                              }
                            })()}
                          </div>
                          <div className="flex flex-col leading-none justify-center ms-3">
                            <span className="text-[1.2em] font-semibold">
                              LAP{" "}
                              {getTyreLife(
                                driver.laps_data,
                                driver.stint_data,
                                currentTime
                              )}
                            </span>

                            <span className="text-[0.87em] opacity-70">
                              STINT{" "}
                              {getStint(
                                driver.laps_data,
                                driver.stint_data,
                                currentTime
                              )}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span
                          className="font-bold h-8 text-xl"
                          style={{
                            color: getPositionsGainedColour(
                              getPositionsGained(
                                driver.positions_data,
                                driver.car_data,
                                currentTime
                              )
                            ),
                          }}
                        >
                          {getPositionsGained(
                            driver.positions_data,
                            driver.car_data,
                            currentTime
                          )}
                        </span>
                      </td>
                      <td>
                        <div className="flex flex-col leading-none">
                          <span
                            className="text-[1.2em] font-semibold"
                            style={{
                              color: getGapTrendColorHex(
                                driver.gap_data,
                                currentTime,
                                "interval"
                              ),
                            }}
                          >
                            {formatGap(
                              getGapToCarAhead(driver.gap_data, currentTime)
                            )}
                          </span>

                          <span className="text-[0.87em] opacity-70">
                            {formatGap(
                              getGapToLeader(driver.gap_data, currentTime)
                            )}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="flex flex-col leading-none">
                          <span
                            className="text-[1.2em] font-semibold"
                            style={{
                              color: getLapTimeColorHex(
                                getLastLapTime(driver.laps_data, currentTime),
                                driver,
                                leaderboardData?.drivers,
                                currentTime
                              ),
                            }}
                          >
                            {formatLapTime(
                              getLastLapTime(driver.laps_data, currentTime)
                            )}
                          </span>

                          <span
                            className="text-[0.87em] opacity-70"
                            style={{
                              color: getLapTimeColorHex(
                                getBestLapTime(driver.laps_data, currentTime),
                                driver,
                                leaderboardData?.drivers,
                                currentTime
                              ),
                            }}
                          >
                            {formatLapTime(
                              getBestLapTime(driver.laps_data, currentTime)
                            )}
                          </span>
                        </div>
                      </td>
                      <td>
                        <SectorWidget
                          driver={driver}
                          allDrivers={leaderboardData?.drivers}
                          currentTime={currentTime}
                          sector={1}
                        />
                      </td>
                      <td>
                        <SectorWidget
                          driver={driver}
                          allDrivers={leaderboardData?.drivers}
                          currentTime={currentTime}
                          sector={2}
                        />
                      </td>
                      <td>
                        <SectorWidget
                          driver={driver}
                          allDrivers={leaderboardData?.drivers}
                          currentTime={currentTime}
                          sector={3}
                        />
                      </td>
                    </motion.tr>
                  ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function getDRSPITStatus(
  pits: LeaderboardPitData[],
  car: LeaderboardCarData[],
  currentTime: number
): string | null {
  if (!car.length) return null;

  if (currentTime < car[0].SessionTime) {
    return "Off";
  }

  const carRow = atOrBefore(car, currentTime);
  if (!carRow) return "Off";

  const pitRow = atOrBefore(pits, currentTime);
  if (
    pitRow &&
    carRow.SessionTime >= pitRow.SessionTime &&
    carRow.SessionTime <= pitRow.SessionTime + pitRow.pit_duration
  ) {
    return "Pit";
  }

  switch (carRow.DRS) {
    case 0:
    case 1:
      return "Off";
    case 8:
      return "Possible";
    case 10:
    case 12:
    case 14:
      return "Active";
    default:
      return "Off";
  }
}

function getCompound(
  pits: LeaderboardPitData[],
  stints: LeaderboardStintData[],
  currentTime: number
): Compound {
  if (!pits.length) return null;
  if (currentTime < pits[0].SessionTime) {
    return stints[0]?.compound ?? "UNKNOWN";
  }

  const pitRow = atOrBefore(pits, currentTime);
  if (!pitRow) return "UNKNOWN";

  const stint = stints.find(
    (s) => pitRow.lap_number >= s.lap_start && pitRow.lap_number <= s.lap_end
  );
  return stint?.compound ?? "UNKNOWN";
}

function getPos(
  positions: LeaderboardPositionsData[],
  currentTime: number
): number | null {
  if (!positions.length) return null;

  if (currentTime < positions[0].SessionTime) {
    return positions[0].position;
  }

  const row = atOrBefore(positions, currentTime);
  return row ? row.position : null;
}

function getTyreLife(
  laps: LeaderboardLapsData[],
  stints: LeaderboardStintData[],
  currentTime: number
): number | null {
  if (!stints.length) return null;

  const lapRow = atOrBefore(laps, currentTime);
  if (!lapRow) return stints[0].tyre_age_at_start;

  const lap = lapRow.lap_number;

  const stint = stints.find((s) => lap >= s.lap_start && lap <= s.lap_end);
  if (!stint) return stints[0].tyre_age_at_start;

  return stint.tyre_age_at_start + (lap - stint.lap_start);
}

function getStint(
  laps: LeaderboardLapsData[],
  stints: LeaderboardStintData[],
  currentTime: number
): number | null {
  if (!stints.length) return null;

  const lapRow = atOrBefore(laps, currentTime);
  if (!lapRow) return stints[0].stint_number;

  const lap = lapRow.lap_number;

  const stint = stints.find((s) => lap >= s.lap_start && lap <= s.lap_end);
  if (!stint) return stints[0].stint_number;

  return stint.stint_number;
}

function getPositionsGained(
  positions: LeaderboardPositionsData[],
  car: LeaderboardCarData[],
  currentTime: number
): string | null {
  if (!car.length) return null;

  if (currentTime < car[0].SessionTime) {
    return null;
  }

  const carRow = atOrBefore(car, currentTime);
  if (!carRow) return null;

  const gridPosition = carRow.grid_position;
  if (gridPosition === 0) return null; // unknown grid position
  const currentPosition = getPos(positions, currentTime);
  if (currentPosition === null) return null;

  const result = gridPosition - currentPosition;
  if (result > 0) {
    return `+${result}`;
  } else if (result < 0) {
    return `${result}`;
  } else {
    return "0";
  }
}

function getGapToCarAhead(
  gap: LeaderboardGapData[],
  currentTime: number
): number | null {
  if (!gap.length) return null;

  if (currentTime < gap[0].SessionTime) {
    return gap[0].interval;
  }

  const row = atOrBefore(gap, currentTime);
  return row ? row.interval : null;
}

function getGapToLeader(
  gap: LeaderboardGapData[],
  currentTime: number
): number | null {
  if (!gap.length) return null;

  if (currentTime < gap[0].SessionTime) {
    return gap[0].gap_to_leader;
  }

  const row = atOrBefore(gap, currentTime);
  return row ? row.gap_to_leader : null;
}

function getLastLapTime(
  laps: LeaderboardLapsData[],
  currentTime: number
): number | null {
  if (!laps.length) return null;

  if (currentTime < laps[0].SessionTime) {
    return laps[0].lap_duration;
  }

  const lap = atOrBefore(laps, currentTime);
  return lap ? lap.lap_duration : null;
}

function getBestLapTime(
  laps: LeaderboardLapsData[],
  currentTime: number
): number | null {
  if (!laps.length) return null;

  // Only laps completed at or before currentTime
  const completed = laps.filter((l) => l.SessionTime <= currentTime);

  if (!completed.length) return null;

  return completed.reduce(
    (best, lap) => Math.min(best, lap.lap_duration),
    Infinity
  );
}

function formatLapTime(seconds: number | null): string {
  if (seconds == null || seconds <= 0) return "—";

  const minutes = Math.floor(seconds / 60);
  const remainder = seconds - minutes * 60;

  const secs = Math.floor(remainder);
  const millis = Math.round((remainder - secs) * 1000);

  return `${minutes}:${secs.toString().padStart(2, "0")}.${millis
    .toString()
    .padStart(3, "0")}`;
}

function formatGap(value: number | null): string {
  if (value == null) return "-";
  if (value === 0) return "LEADER";

  const sign = value > 0 ? "+" : "-";
  return `${sign}${Math.abs(value).toFixed(3)}`;
}

function getPositionsGainedColour(pg: string | null | undefined) {
  if (!pg) return "inherit";
  if (pg.startsWith("+")) return "#00c851"; // green
  if (pg.startsWith("-")) return "#ff4444"; // red;
  return "inherit"; // "0"
}

// F1 universal-ish colours (common across timing UIs)
const LAP_PURPLE = "#A855F7"; // session best
const LAP_GREEN = "#22C55E"; // personal best
const LAP_NEUTRAL = "#E5E7EB"; // normal/unknown (light grey)
const LAP_DIM = "#9CA3AF"; // no data / invalid

function getLapTimeColorHex(
  displayedLapTime: number | null, // the number you are showing (last lap OR best lap)
  driver: LeaderboardDriverData,
  allDrivers: LeaderboardDriverData[],
  currentTime: number
): string {
  if (displayedLapTime == null || displayedLapTime <= 0) return LAP_DIM;

  const displayedMs = Math.round(displayedLapTime * 1000);

  // Driver best so far (PB) up to currentTime
  const driverBestMs = getDriverBestLapMsSoFar(driver.laps_data, currentTime);
  if (driverBestMs == null) return LAP_DIM;

  // Session best so far up to currentTime (across all drivers)
  const sessionBestMs = getSessionBestLapMsSoFar(allDrivers, currentTime);
  if (sessionBestMs == null) return LAP_DIM;

  if (displayedMs === sessionBestMs) return LAP_PURPLE;
  if (displayedMs === driverBestMs) return LAP_GREEN;

  return LAP_NEUTRAL;
}

function getDriverBestLapMsSoFar(
  laps: LeaderboardLapsData[],
  currentTime: number
): number | null {
  let best = Infinity;

  for (const l of laps) {
    if (l.SessionTime > currentTime) continue; // order-independent
    if (l.lap_duration <= 0) continue;
    if (l.is_pit_out_lap) continue;
    const ms = Math.round(l.lap_duration * 1000);
    if (ms < best) best = ms;
  }

  return best === Infinity ? null : best;
}

function getSessionBestLapMsSoFar(
  drivers: LeaderboardDriverData[],
  currentTime: number
): number | null {
  let best = Infinity;

  for (const d of drivers) {
    for (const l of d.laps_data) {
      if (l.SessionTime > currentTime) continue; // order-independent
      if (l.lap_duration <= 0) continue;
      if (l.is_pit_out_lap) continue;
      const ms = Math.round(l.lap_duration * 1000);
      if (ms < best) best = ms;
    }
  }

  return best === Infinity ? null : best;
}

function getGapTrendColorHex(
  gap: LeaderboardGapData[],
  currentTime: number,
  kind: "interval" | "leader",
  epsilon = 0.001
): string {
  if (!gap.length) return "#9CA3AF"; // neutral

  const currentRow =
    currentTime < gap[0].SessionTime ? gap[0] : atOrBefore(gap, currentTime);
  if (!currentRow) return "#9CA3AF";

  const currentValue =
    kind === "interval" ? currentRow.interval : currentRow.gap_to_leader;

  // No trend color if leader/invalid
  if (currentValue == null) return "#9CA3AF";

  // Find previous row (strictly before currentRow)
  const idx = gap.findIndex((g) => g.SessionTime === currentRow.SessionTime);
  const prevRow = idx > 0 ? gap[idx - 1] : null;

  if (!prevRow) return "#9CA3AF";

  const prevValue =
    kind === "interval" ? prevRow.interval : prevRow.gap_to_leader;

  if (prevValue == null) return "#9CA3AF";

  const delta = currentValue - prevValue;

  if (Math.abs(delta) <= epsilon) return "#9CA3AF"; // stable
  return delta < 0 ? "#22C55E" : "#EF4444"; // closing : opening
}

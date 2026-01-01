import React, { useEffect, useState } from "react";
import type {
  LeaderboardApiResponse,
  LeaderboardPositionsData,
  LeaderboardLapsData,
  LeaderboardStintData,
  LeaderboardPitData,
  Compound,
  LeaderboardCarData,
} from "../types";
import { motion, AnimatePresence } from "framer-motion";
import hardTyre from "../assets/hard.svg";
import intermediateTyre from "../assets/intermediate.svg";
import mediumTyre from "../assets/medium.svg";
import softTyre from "../assets/soft.svg";
import unknownTyre from "../assets/unknown.svg";
import wetTyre from "../assets/wet.svg";

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
        <h2 className="card-title">Leaderboard</h2>
        <table className="table mt-5">
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
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
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
                                return <img src={mediumTyre} className="h-8" />;

                              case "INTERMEDIATE":
                                return (
                                  <img src={intermediateTyre} className="h-8" />
                                );

                              case "HARD":
                                return <img src={hardTyre} className="h-8" />;

                              default:
                                return null;
                            }
                          })()}
                        </div>
                        <div className="ms-3">
                          <p>
                            LAP{" "}
                            {getTyreLife(
                              driver.laps_data,
                              driver.stint_data,
                              currentTime
                            )}
                          </p>
                          <p>
                            STINT{" "}
                            {getStint(
                              driver.laps_data,
                              driver.stint_data,
                              currentTime
                            )}
                          </p>
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
                  </motion.tr>
                ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function atOrBefore<T extends { SessionTime: number }>(
  rows: T[],
  currentTime: number
): T | null {
  if (!rows.length) return null;
  if (currentTime < rows[0].SessionTime) return null;

  let lo = 0,
    hi = rows.length - 1,
    ans = -1;

  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (rows[mid].SessionTime <= currentTime) {
      ans = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }

  return ans >= 0 ? rows[ans] : null;
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

function getPositionsGainedColour(pg: string | null | undefined) {
  if (!pg) return "inherit";
  if (pg.startsWith("+")) return "#00c851"; // green
  if (pg.startsWith("-")) return "#ff4444"; // red;
  return "inherit"; // "0"
}

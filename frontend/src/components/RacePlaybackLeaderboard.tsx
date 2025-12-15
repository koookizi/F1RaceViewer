import React, { useEffect, useState } from "react";
import type {
  SessionLeaderboardResponse,
  DriverData,
  LapData,
  TelemetryDriverMap,
  TelemetrySample,
} from "../types";
import { motion, AnimatePresence } from "framer-motion";
import hardTyre from "../assets/hard.svg";
import intermediateTyre from "../assets/intermediate.svg";
import mediumTyre from "../assets/medium.svg";
import softTyre from "../assets/soft.svg";
import unknownTyre from "../assets/unknown.svg";
import wetTyre from "../assets/wet.svg";

type RacePlaybackLeaderboardProps = {
  year: number;
  country: string;
  session: string;
  currentTime: number;
};

export function RacePlaybackLeaderboard({
  year,
  country,
  session,
  currentTime,
}: RacePlaybackLeaderboardProps) {
  const [lapsData, setLapsData] = useState<SessionLeaderboardResponse | null>(
    null
  );
  const [telemetry, setTelemetry] = useState<TelemetryDriverMap | null>(null);

  const DRSTest = "Active";

  useEffect(() => {
    const url = `http://localhost:8000/api/session/${year}/${encodeURIComponent(
      country
    )}/${encodeURIComponent(session)}/laps/`;

    console.log("Fetching leaderboard from:", url);

    fetch(url)
      .then((res) => res.json())
      .then((json: SessionLeaderboardResponse) => {
        console.log("Leaderboard JSON:", json);
        setLapsData(json);
      })
      .catch((err) => {
        console.error("Failed to load leaderboard data", err);
      });
  }, [year, country, session]);

  useEffect(() => {
    const url = `http://localhost:8000/api/session/${year}/${encodeURIComponent(
      country
    )}/${encodeURIComponent(session)}/telemetry/`;

    console.log("Fetching telemetry from:", url);

    fetch(url)
      .then((res) => res.json())
      .then((json: TelemetryDriverMap) => {
        console.log("Telemetry JSON:", json);
        setTelemetry(json);
      })
      .catch((err) => {
        console.error("Failed to load telemetry data", err);
      });
  }, [year, country, session]);

  if (!lapsData || !telemetry) {
    return <div className="skeleton h-32 w-auto mt-5"></div>;
  }
  return (
    <div className="card card-border bg-base-100 mt-5 ">
      <div className="card-body">
        <h2 className="card-title">Leaderboard</h2>
        <table className="table mt-5">
          <thead></thead>
          <tbody>
            <AnimatePresence initial={false}>
              {lapsData?.drivers
                .slice()
                .sort(
                  (a, b) =>
                    (getPos(telemetry, a, currentTime) ?? 9999) -
                    (getPos(telemetry, b, currentTime) ?? 9999)
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
                          backgroundColor: `#${driver.teamColour}`,
                          color: `color-mix(in srgb, #${driver.teamColour} 20%, black)`,
                          filter: "brightness(0.8)",
                          border: 0,
                        }}
                      >
                        {getPos(telemetry, driver, currentTime)}
                        <div
                          className="badge font-bold"
                          style={{
                            backgroundColor: "white",
                            color: `#${driver.teamColour}`,
                            border: 0,
                          }}
                        >
                          {driver.driver_code}
                        </div>
                      </div>
                    </td>
                    <td>
                      {(() => {
                        switch (DRSTest) {
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
                            switch (getCompound(driver, currentTime)) {
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
                          <p>LAP {getTyreLife(driver, currentTime)}</p>
                          <p>STINT {getStint(driver, currentTime)}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span
                        className="font-bold h-8 text-xl"
                        style={{
                          color: getPositionsGainedColour(
                            getPositionsGained(driver, currentTime)
                          ),
                        }}
                      >
                        {getPositionsGained(driver, currentTime)}
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

function getCompound(driver: DriverData, t: number) {
  const idx = driver.data.findIndex(
    (row) =>
      row.LapStartTime != null &&
      row.Time != null &&
      t >= row.LapStartTime &&
      t < row.Time
  );

  const currentCompoundRow = idx !== -1 ? driver.data[idx] : null;
  let previousRow: LapData | null;
  try {
    previousRow = idx > 0 ? driver.data[idx - 1] : null;
  } catch {
    previousRow = idx !== -1 ? driver.data[idx] : null;
  }

  if (currentCompoundRow?.FreshTyre && t >= currentCompoundRow.PitOutTime) {
    return currentCompoundRow?.Compound;
  } else {
    return previousRow?.Compound;
  }
}

function getPos(
  telemetry: TelemetryDriverMap,
  driver: DriverData,
  t: number
): number | null {
  const samples = telemetry[driver.driver_code];
  if (!samples || samples.length === 0) return null;

  const binSize = samples[0].TimeBinSize;
  const targetBin = Math.round(t / binSize);

  // samples must be sorted by TimeBin (they should be from backend)
  for (let i = samples.length - 1; i >= 0; i--) {
    if (samples[i].TimeBin <= targetBin) {
      return samples[i].LivePosition ?? null;
    }
  }

  return null;
}

function getTyreLife(driver: DriverData, t: number) {
  return driver.data.find((row) => t >= row.LapStartTime && t < row.Time)
    ?.TyreLife;
}

function getStint(driver: DriverData, t: number) {
  const idx = driver.data.findIndex(
    (row) =>
      row.LapStartTime != null &&
      row.Time != null &&
      t >= row.LapStartTime &&
      t < row.Time
  );

  const currentStintRow = idx !== -1 ? driver.data[idx] : null;
  let previousRow: LapData | null;
  try {
    previousRow = idx > 0 ? driver.data[idx - 1] : null;
  } catch {
    previousRow = idx !== -1 ? driver.data[idx] : null;
  }

  if (currentStintRow?.FreshTyre && t >= currentStintRow.PitOutTime) {
    return currentStintRow?.Stint;
  } else {
    return previousRow?.Stint;
  }
}

function getPositionsGained(driver: DriverData, t: number) {
  return driver.data.find((row) => t >= row.LapStartTime && t < row.Time)
    ?.PositionsGained;
}

function getPositionsGainedColour(pg: string | null | undefined) {
  if (!pg) return "inherit";
  if (pg.startsWith("+")) return "#00c851"; // green
  if (pg.startsWith("-")) return "#ff4444"; // red;
  return "inherit"; // "0"
}

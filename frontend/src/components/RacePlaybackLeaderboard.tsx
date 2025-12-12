import React, { useEffect, useState } from "react";
import type { SessionLeaderboardResponse, DriverData } from "../types";
import { motion, AnimatePresence } from "framer-motion";

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
  const [data, setData] = useState<SessionLeaderboardResponse | null>(null);

  useEffect(() => {
    const url = `http://localhost:8000/api/session/${year}/${encodeURIComponent(
      country
    )}/${encodeURIComponent(session)}/leaderboard/`;

    console.log("Fetching leaderboard from:", url);

    fetch(url)
      .then((res) => res.json())
      .then((json: SessionLeaderboardResponse) => {
        console.log("Leaderboard JSON:", json);
        setData(json);
      })
      .catch((err) => {
        console.error("Failed to load leaderboard data", err);
      });
  }, [year, country, session]);

  if (!data) {
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
              {data?.drivers
                .slice()
                .sort(
                  (a, b) =>
                    (getPos(a, currentTime) ?? 9999) -
                    (getPos(b, currentTime) ?? 9999)
                )
                .map((driver) => (
                  <motion.tr
                    key={driver.driver_code}
                    layout // <- this is what animates the movement
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    style={{
                      backgroundColor: "#" + driver.teamColour + "33",
                    }}
                  >
                    <td>{getPos(driver, currentTime)}</td>
                    <td>{driver.driver_code}</td>
                    <td>{getLapNumber(driver, currentTime)}</td>
                    <td>{getCurrentTyre(driver, currentTime)}</td>
                  </motion.tr>
                ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function getLapNumber(driver: DriverData, t: number) {
  return driver.data.find((row) => t >= row.LapStartTime && t < row.Time)
    ?.LapNumber;
}

function getCurrentTyre(driver: DriverData, t: number) {
  return driver.data.find((row) => t >= row.LapStartTime && t < row.Time)
    ?.Compound;
}

function getPos(driver: DriverData, t: number) {
  return driver.data.find((row) => t >= row.LapStartTime && t < row.Time)
    ?.Position;
}

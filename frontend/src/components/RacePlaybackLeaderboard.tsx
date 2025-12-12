import React, { useEffect, useState } from "react";
import type { SessionLeaderboardResponse } from "../types";

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
      .then((res) => {
        if (!res.ok) {
          // This will show 404/500/etc
          throw new Error(`HTTP ${res.status} ${res.statusText}`);
        }
        return res.json();
      })
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
        <div>hi</div>
      </div>
    </div>
  );
}

function getDataAtTime(data: any[], t: number) {
  return data;
}

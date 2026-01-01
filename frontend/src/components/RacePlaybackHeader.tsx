import React, { useEffect, useState } from "react";
import type { WeatherApiResponse, PlaybackData } from "../types";
import { WeatherInfo } from "../components/RacePlaybackWeatherInfo";
import { getPositionAtTime } from "../helpers/playback";

type RacePlaybackHeaderProps = {
  weatherData: WeatherApiResponse | null;
  playbackData: PlaybackData | null;
  currentTime: number;
  circuitName: string;
  selectedYear: string;
  selectedSession: string;
};

export function RacePlaybackHeader({
  weatherData,
  playbackData,
  currentTime,
  circuitName,
  selectedYear,
  selectedSession,
}: RacePlaybackHeaderProps) {
  if (!weatherData || !playbackData) {
    return <div className="skeleton h-24 w-auto mt-2"></div>;
  }

  const { raceDuration, totalLaps, drivers, playbackControlOffset } =
    playbackData;

  const leader = drivers[0];
  const leaderPos = leader
    ? getPositionAtTime(leader.samples, currentTime)
    : null;
  const currentLap = leaderPos?.lap ?? 1;

  return (
    <div className="card card-border bg-base-100 w-full">
      <div className="card-body p-3">
        <div className="grid grid-cols-3 gap-2">
          <div className="col-span-1 p-3">
            <h2 className="card-title">
              {circuitName.toUpperCase()} {selectedYear} GRAND PRIX -{" "}
              {selectedSession.toUpperCase()}
            </h2>
          </div>
          <div className="col-span-1">
            <WeatherInfo weatherData={weatherData} currentTime={currentTime} />
          </div>
          <div className="col-span-1 p-3">
            <div className="flex items-center justify-end h-full text-right">
              <span className="text-4xl leading-none font-bold">
                {currentLap} / {totalLaps}
              </span>{" "}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

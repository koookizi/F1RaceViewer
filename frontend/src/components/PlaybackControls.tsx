// src/components/PlaybackControls.tsx
import React from "react";
import type { PlaybackData } from "../types";
import { getPositionAtTime } from "../helpers/playback";

type PlaybackControlsProps = {
  data: PlaybackData | null;
  currentTime: number;
  setCurrentTime: (value: number) => void;

  isPlaying: boolean;
  setIsPlaying: (value: boolean | ((prev: boolean) => boolean)) => void;

  speedMultiplier: number;
  setSpeedMultiplier: (value: number) => void;
};

export function PlaybackControls({
  data,
  currentTime,
  setCurrentTime,
  isPlaying,
  setIsPlaying,
  speedMultiplier,
  setSpeedMultiplier,
}: PlaybackControlsProps) {
  if (!data) {
    return <div className="skeleton h-24 w-auto mt-2"></div>;
  }

  const { raceDuration, totalLaps, drivers } = data;

  const leader = drivers[0];
  const leaderPos = leader
    ? getPositionAtTime(leader.samples, currentTime)
    : null;
  const currentLap = leaderPos?.lap ?? 1;

  const handleScrub = (value: number) => {
    setCurrentTime(value);
  };

  return (
    <div className="card card-border bg-base-100">
      <div className="card-body">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <button
              className="btn px-3 py-1 rounded bg-neutral-600 text-white text-sm"
              onClick={() => setIsPlaying((p) => !p)}
            >
              {isPlaying ? "Pause" : "Play"}
            </button>

            <div className="tabs tabs-box">
              <input
                type="radio"
                onClick={() => setSpeedMultiplier(1)}
                name="playback_speed"
                className="tab"
                aria-label="x1"
                defaultChecked={speedMultiplier === 1}
              />
              <input
                type="radio"
                onClick={() => setSpeedMultiplier(5)}
                name="playback_speed"
                className="tab"
                aria-label="x5"
              />
              <input
                type="radio"
                onClick={() => setSpeedMultiplier(20)}
                name="playback_speed"
                className="tab"
                aria-label="x20"
              />
              <input
                type="radio"
                onClick={() => setSpeedMultiplier(50)}
                name="playback_speed"
                className="tab"
                aria-label="x50"
              />
            </div>

            <span className="text-sm text-gray-300">
              t = {currentTime.toFixed(1)}s / {raceDuration.toFixed(1)}s
            </span>
            <span className="text-sm text-gray-300">
              Lap {currentLap} / {totalLaps}
            </span>
          </div>

          {/* slider */}
          <input
            type="range"
            min={0}
            max={raceDuration}
            step={0.2}
            value={currentTime}
            onChange={(e) => handleScrub(parseFloat(e.target.value))}
            className="w-full range range-neutral bg-neutral-800"
          />
        </div>
      </div>
    </div>
  );
}

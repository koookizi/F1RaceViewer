// src/components/PlaybackControls.tsx
import React from "react";
import type { PlaybackData } from "../types";
import { getPositionAtTime, formatWallClockTime } from "../helpers/playback";

type PlaybackControlsProps = {
    data: PlaybackData | null;
    currentTime: number;
    setCurrentTime: (value: number) => void;

    isPlaying: boolean;
    setIsPlaying: (value: boolean | ((prev: boolean) => boolean)) => void;

    speedMultiplier: number;
    setSpeedMultiplier: (value: number) => void;

    sessionStart: string;

    setIsScrubbing: (v: boolean) => void;
    triggerTeamRadioAutoplay: () => void;
};

export function PlaybackControls({
    data,
    currentTime,
    sessionStart,
    setCurrentTime,
    isPlaying,
    setIsPlaying,
    speedMultiplier,
    setSpeedMultiplier,
    setIsScrubbing,
    triggerTeamRadioAutoplay,
}: PlaybackControlsProps) {
    if (!data) {
        return <div className="skeleton h-24 w-auto mt-2"></div>;
    }

    const { raceDuration, totalLaps, drivers, playbackControlOffset } = data;

    const leader = drivers[0];
    const leaderPos = leader ? getPositionAtTime(leader.samples, currentTime) : null;
    const currentLap = leaderPos?.lap ?? 1;

    const handleScrub = (value: number) => {
        setCurrentTime(value);
    };

    return (
        <div className="fixed bottom-0 inset-x-0 z-50 border-t border-neutral-700 bg-base-100/95 backdrop-blur">
            <div className="max-w-7xl mx-auto px-4 py-3">
                <div className="flex flex-col gap-2">
                    {/* Top row */}
                    <div className="flex flex-wrap items-center gap-3">
                        <button
                            className="btn btn-sm px-4 bg-neutral-600 text-white"
                            onClick={() => setIsPlaying((p) => !p)}
                        >
                            {isPlaying ? "Pause" : "Play"}
                        </button>

                        <div className="tabs tabs-boxed tabs-sm">
                            <input
                                type="radio"
                                name="playback_speed"
                                className="tab"
                                aria-label="x1"
                                onClick={() => setSpeedMultiplier(1)}
                                defaultChecked={speedMultiplier === 1}
                            />
                            <input
                                type="radio"
                                name="playback_speed"
                                className="tab"
                                aria-label="x5"
                                onClick={() => setSpeedMultiplier(5)}
                            />
                            <input
                                type="radio"
                                name="playback_speed"
                                className="tab"
                                aria-label="x20"
                                onClick={() => setSpeedMultiplier(20)}
                            />
                            <input
                                type="radio"
                                name="playback_speed"
                                className="tab"
                                aria-label="x50"
                                onClick={() => setSpeedMultiplier(50)}
                            />
                        </div>

                        <div className="ml-auto flex gap-4 text-sm text-gray-300">
                            <span>{formatWallClockTime(sessionStart, currentTime)}</span>
                            <span>
                                Lap {currentLap} / {totalLaps}
                            </span>
                        </div>
                    </div>

                    {/* Scrubber */}
                    <input
                        type="range"
                        min={playbackControlOffset}
                        max={raceDuration}
                        step={0.2}
                        value={currentTime}
                        onChange={(e) => handleScrub(parseFloat(e.target.value))}
                        onMouseDown={() => setIsScrubbing(true)}
                        onMouseUp={() => {
                            setIsScrubbing(false);
                            triggerTeamRadioAutoplay(); // ✅ scrub finished → autoplay first
                        }}
                        onTouchStart={() => setIsScrubbing(true)}
                        onTouchEnd={() => {
                            setIsScrubbing(false);
                            triggerTeamRadioAutoplay(); // ✅ scrub finished → autoplay first
                        }}
                        className="range range-neutral w-full"
                    />
                </div>
            </div>
        </div>
    );
}

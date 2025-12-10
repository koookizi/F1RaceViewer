// RacePlayback.tsx
import React, { useEffect, useState, useRef } from "react";
import type { PlaybackData } from "../types";

type Props = {
  year: number;
  country: string;
  session: string;
};

export function RacePlayback({ year, country, session }: Props) {
  const [data, setData] = useState<PlaybackData | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const lastFrameRef = useRef<number | null>(null);

  // Fetch playback data
  useEffect(() => {
    const url = `http://localhost:8000/api/session/${year}/${encodeURIComponent(
      country
    )}/${encodeURIComponent(session)}/playback/`;
    fetch(url)
      .then((res) => res.json())
      .then((json: PlaybackData) => {
        setData(json);
        setCurrentTime(0);
      })
      .catch((err) => console.error("Failed to load playback", err));
  }, [year, country, session]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !data) return;

    // gives us the current time (irl time) of when the playback started
    const start = performance.now() - currentTime * 1000;

    // gets called by requestAnimationFrame to update, per frame
    const tick = (now: number) => {
        // this tells us how far in we are into the playback
        // why not store a global var instead? can't because react refreshes etc.
        const elapsedSec = (now - start) / 1000;

        // just a clamp so it never goes past raceDuration/the playback
        const t = Math.min(elapsedSec, data.raceDuration);

        // sets the currentTime variable
        setCurrentTime(t);
        // because of this changing, it will trigger the getPositionAtTime() func through const pos

        // this is what makes tick loop. but obvs if not playing or no data, this useEffect will stop this loop
        if (t < data.raceDuration) {
            lastFrameRef.current = requestAnimationFrame(tick);
        } else {
            setIsPlaying(false);
        }
    };

    // starts the loop, once started it'll keep recursively going
    lastFrameRef.current = requestAnimationFrame(tick);

    // cleans up the animation whenever you pause, switch tab, or load different race
    return () => {
      if (lastFrameRef.current !== null) {
        cancelAnimationFrame(lastFrameRef.current);
      }
    };
  }, [isPlaying, data]);

  // when slider is dragged, onChange fires
  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    // gets the slider's value and sets it to the currentTime var, then re-renders because currentTime was set
    setCurrentTime(parseFloat(e.target.value));
  };

  if (!data) {
    return <div>Loading playback…</div>;
  }

  const { track, drivers, raceDuration, totalLaps } = data;

  // simple lap indicator: current lap of leader (first driver)
  const leader = drivers[0];
  const leaderPos = leader ? getPositionAtTime(leader.samples, currentTime) : null;
  const currentLap = leaderPos?.lap ?? 1;

  return (
    <div className="flex flex-col gap-4">
      {/* Track + cars */}
      <div className="w-full flex justify-center">
        <svg
          viewBox="-1.2 -1.2 2.4 2.4"
          className="w-full max-w-3xl border rounded-xl bg-neutral-900"
        >
          {/* Track polyline */}
          <polyline
            fill="none"
            stroke="#555"
            strokeWidth={0.01}
            points={track.points.map(([x, y]) => `${x},${-y}`).join(" ")} // flip Y for SVG
          />

          {/* Driver dots */}
          {drivers.map((drv) => {
            const pos = getPositionAtTime(drv.samples, currentTime);
            if (!pos) return null;
            return (
              <circle
                key={drv.code}
                cx={pos.x}
                cy={-pos.y}
                r={0.02}
                fill={drv.color || "white"}
              >
                <title>{drv.code}</title>
              </circle>
            );
          })}
        </svg>
      </div>

      {/* Playback controls */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white text-sm"
            onClick={() => setIsPlaying((p) => !p)}
          >
            {isPlaying ? "Pause" : "Play"}
          </button>
          <span className="text-sm text-gray-300">
            t = {currentTime.toFixed(1)}s / {raceDuration.toFixed(1)}s
          </span>
          <span className="text-sm text-gray-300">Lap {currentLap} / {totalLaps}</span>
        </div>

        {/* Scrub bar over race time */}
        <input
          type="range"
          min={0}
          max={raceDuration}
          step={0.2}
          value={currentTime}
          onChange={handleScrub}
          className="w-full"
        />

        {/* “Split into laps” visually */}
        <div className="relative h-2 bg-neutral-800 rounded overflow-hidden">
          {Array.from({ length: totalLaps - 1 }).map((_, i) => (
            <div
              key={i}
              className="absolute top-0 bottom-0 border-r border-neutral-600"
              style={{ left: `${((i + 1) / totalLaps) * 100}%` }}
            />
          ))}
          <div
            className="absolute top-0 bottom-0 bg-blue-500/40"
            style={{ width: `${(currentTime / raceDuration) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

// reuse interpolation function
function getPositionAtTime(samples: any[], t: number) {
  if (!samples.length) return null;
  if (t <= samples[0].t) return samples[0];
  if (t >= samples[samples.length - 1].t) return samples[samples.length - 1];

  for (let i = 0; i < samples.length - 1; i++) {
    const a = samples[i];
    const b = samples[i + 1];
    if (t >= a.t && t <= b.t) {
      const ratio = (t - a.t) / (b.t - a.t || 1);
      return {
        t,
        lap: a.lap,
        x: a.x + (b.x - a.x) * ratio,
        y: a.y + (b.y - a.y) * ratio,
      };
    }
  }
  return samples[samples.length - 1];
}
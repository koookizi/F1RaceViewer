import React, { useEffect, useRef, useState } from "react";

type AudioPlaybackBarProps = {
  src: string;
  className?: string;
  autoPlayEnabled: boolean;
  autoPlayToken: number;
};

export function AudioPlaybackBar({
  src,
  className,
  autoPlayEnabled,
  autoPlayToken,
}: AudioPlaybackBarProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastAutoPlayTokenRef = useRef<number | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0); // seconds
  const [current, setCurrent] = useState(0); // seconds
  const [isSeeking, setIsSeeking] = useState(false);

  // Create / destroy audio only when src changes
  useEffect(() => {
    const audio = new Audio(src);
    audioRef.current = audio;

    // reset state for new src
    setIsPlaying(false);
    setDuration(0);
    setCurrent(0);
    lastAutoPlayTokenRef.current = null;

    const onLoaded = () => setDuration(audio.duration || 0);
    const onTime = () => {
      if (!isSeeking) setCurrent(audio.currentTime || 0);
    };
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener("loadedmetadata", onLoaded);
    audio.addEventListener("timeupdate", onTime);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.pause();
      audio.src = "";
      audio.removeEventListener("loadedmetadata", onLoaded);
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("ended", onEnded);
      if (audioRef.current === audio) audioRef.current = null;
    };
    // include isSeeking so the handler reads the latest value (safe)
  }, [src, isSeeking]);

  // Autoplay ONLY when token bumps, and only if enabled
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (!autoPlayEnabled) return;

    // only once per token bump
    if (lastAutoPlayTokenRef.current === autoPlayToken) return;
    lastAutoPlayTokenRef.current = autoPlayToken;

    // start from beginning (optional)
    audio.currentTime = 0;

    audio.play().catch(() => {
      // browser may block autoplay; ignore
    });
  }, [autoPlayEnabled, autoPlayToken]);

  const togglePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    try {
      if (audio.paused) await audio.play();
      else audio.pause();
    } catch {
      // autoplay restrictions / transient errors
    }
  };

  const seekTo = (value: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = value;
    setCurrent(value);
  };

  return (
    <div className={`flex items-center gap-2 w-full ${className ?? ""}`}>
      <button
        type="button"
        className="btn btn-ghost btn-xs"
        aria-label={isPlaying ? "Pause" : "Play"}
        onClick={togglePlay}
      >
        {isPlaying ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            className="h-4 w-4"
            fill="currentColor"
          >
            <path d="M6 5h4v14H6V5zm8 0h4v14h-4V5z" />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            className="h-4 w-4"
            fill="currentColor"
          >
            <path d="M8 5v14l11-7L8 5z" />
          </svg>
        )}
      </button>

      <input
        type="range"
        min={0}
        max={Math.max(duration, 0)}
        step={0.01}
        value={Math.min(current, duration || 0)}
        onMouseDown={() => setIsSeeking(true)}
        onMouseUp={() => setIsSeeking(false)}
        onTouchStart={() => setIsSeeking(true)}
        onTouchEnd={() => setIsSeeking(false)}
        onChange={(e) => seekTo(parseFloat(e.target.value))}
        className="range range-xs range-neutral flex-1"
      />
    </div>
  );
}

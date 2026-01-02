import React, { useEffect, useRef, useState } from "react";

type AudioPlaybackBarProps = {
  src: string;
  className?: string;
  teamRadioAutoplay: boolean;
};

export function AudioPlaybackBar({
  src,
  className,
  teamRadioAutoplay,
}: AudioPlaybackBarProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0); // seconds
  const [current, setCurrent] = useState(0); // seconds
  const [isSeeking, setIsSeeking] = useState(false);

  useEffect(() => {
    const audio = new Audio(src);
    audioRef.current = audio;

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

    if (teamRadioAutoplay) {
      audio.play().catch(() => {
        // browser blocked it (safe to ignore)
      });
    }

    return () => {
      audio.pause();
      audio.src = "";
      audio.removeEventListener("loadedmetadata", onLoaded);
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("ended", onEnded);
      audioRef.current = null;
    };
  }, [src]);

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
          // pause icon
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            className="h-4 w-4"
            fill="currentColor"
          >
            <path d="M6 5h4v14H6V5zm8 0h4v14h-4V5z" />
          </svg>
        ) : (
          // play icon
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

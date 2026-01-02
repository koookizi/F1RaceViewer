import React, { useEffect, useMemo, useRef, useState } from "react";
import type {
  LeaderboardApiResponse,
  RaceControlApiResponse,
  TeamRadioApiResponse,
} from "../types";
import { AnimatePresence, motion } from "framer-motion";
import { getDriverAbbreviation } from "../helpers/driver_identifiers";
import { teamBgByDriver } from "../helpers/team_colour";
import { AudioPlaybackBar } from "../components/AudioPlaybackBar";

type RacePlaybackTeamRadioProps = {
  teamRadioData: TeamRadioApiResponse[] | null;
  leaderboardData: LeaderboardApiResponse | null;
  currentTime: number;
  teamRadioAutoplay: boolean;
  setTeamRadioAutoplay: React.Dispatch<React.SetStateAction<boolean>>;
  isScrubbing: boolean;
  teamRadioAutoplayToken: number;
};

export function RacePlaybackTeamRadio({
  teamRadioData,
  currentTime,
  leaderboardData,
  teamRadioAutoplay,
  setTeamRadioAutoplay,
  isScrubbing,
  teamRadioAutoplayToken,
}: RacePlaybackTeamRadioProps) {
  if (!teamRadioData) {
    return <div className="skeleton h-24 w-auto"></div>;
  }

  const messages = useMemo(
    () => getTeamRadioAtTime(teamRadioData, currentTime),
    [teamRadioData, currentTime]
  );

  const seenKeysRef = useRef<Set<string>>(new Set());

  const [pulseKeys, setPulseKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    const nextPulse = new Set<string>();

    for (const msg of messages) {
      const key = teamRadioKey(msg);
      if (!seenKeysRef.current.has(key)) {
        nextPulse.add(key);
        seenKeysRef.current.add(key);
      }
    }

    setPulseKeys(nextPulse);
  }, [messages]);

  return (
    <div className="card card-border bg-base-100 w-full">
      <div className="card-body p-3 max-h-80 overflow-y-auto">
        <ul className="list bg-base-100 rounded-box shadow-md">
          <li className="p-4 pb-2 text-xs opacity-60 tracking-wide flex items-center">
            <span>Team Radio</span>

            <button
              type="button"
              className={`btn btn-sm transition ml-auto ${
                teamRadioAutoplay ? "btn-success btn-active" : "btn-ghost"
              }`}
              onClick={() => setTeamRadioAutoplay((v) => !v)}
              aria-pressed={teamRadioAutoplay}
              title="Toggle team radio autoplay"
            >
              {teamRadioAutoplay ? "Autoplay ON" : "Autoplay OFF"}
            </button>
          </li>

          <AnimatePresence initial={false}>
            {messages.map((msg, index) => {
              const key = teamRadioKey(msg);
              const shouldPulse = pulseKeys.has(key);

              return (
                <motion.li
                  key={key}
                  className="list-row"
                  initial={{ opacity: 0, y: -8 }}
                  animate={
                    shouldPulse
                      ? {
                          opacity: 1,
                          y: 0,
                          scale: [1, 1.03, 1],
                          filter: [
                            "brightness(1)",
                            "brightness(1.25)",
                            "brightness(1)",
                          ],
                        }
                      : { opacity: 1, y: 0 }
                  }
                  exit={{ opacity: 0, y: 8 }}
                  transition={{
                    type: "spring",
                    stiffness: 400,
                    damping: 28,
                    scale: { duration: 0.6 },
                    filter: { duration: 0.6 },
                  }}
                >
                  <div className="list-col-grow">
                    <div className="flex flex-col">
                      {/* Time */}
                      <div className="text-xs uppercase font-semibold opacity-60 mb-2">
                        {msg.time}
                      </div>

                      <div className="flex items-center gap-3">
                        {/* Driver badge */}
                        <div
                          className="badge font-bold flex py-4 inline-flex px-1 leading-none"
                          style={{
                            backgroundColor: teamBgByDriver(
                              leaderboardData,
                              msg.driver_number,
                              "opaque"
                            ),
                            color: `color-mix(in srgb, ${teamBgByDriver(
                              leaderboardData,
                              msg.driver_number,
                              "opaque"
                            )} 20%, black)`,
                            border: 0,
                          }}
                        >
                          <span
                            className="badge font-bold"
                            style={{
                              backgroundColor: "white",
                              color: teamBgByDriver(
                                leaderboardData,
                                msg.driver_number,
                                "opaque"
                              ),
                              border: 0,
                            }}
                          >
                            {getDriverAbbreviation(
                              leaderboardData,
                              msg.driver_number
                            )}
                          </span>
                        </div>

                        {/* Playback bar */}
                        <div className="flex-1 flex items-center">
                          <AudioPlaybackBar
                            src={msg.recording_url}
                            autoPlayEnabled={
                              teamRadioAutoplay && !isScrubbing && index === 0
                            }
                            autoPlayToken={teamRadioAutoplayToken}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
      </div>
    </div>
  );
}

function getTeamRadioAtTime(
  teamRadioData: TeamRadioApiResponse[] | null,
  currentTime: number
): TeamRadioApiResponse[] {
  if (!teamRadioData?.length) return [];

  return teamRadioData
    .filter((radio) => radio.SessionTime <= currentTime)
    .sort((a, b) => b.SessionTime - a.SessionTime); // newest first
}

function teamRadioKey(radio: TeamRadioApiResponse): string {
  return `${radio.SessionTime}-${radio.driver_number ?? "NA"}-${
    radio.recording_url
  }`;
}

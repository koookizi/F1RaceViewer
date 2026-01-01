import React, { useEffect, useMemo, useRef, useState } from "react";
import type { RaceControlApiResponse } from "../types";
import { AnimatePresence, motion } from "framer-motion";
import { RaceControlFlag } from "../components/RaceControlFlag";

type RacePlaybackRaceControlProps = {
  raceControlData: RaceControlApiResponse[] | null;
  currentTime: number;
};

export function RacePlaybackRaceControl({
  raceControlData,
  currentTime,
}: RacePlaybackRaceControlProps) {
  if (!raceControlData) {
    return <div className="skeleton h-24 w-auto"></div>;
  }

  const messages = useMemo(
    () => getRaceControlMessagesAtTime(raceControlData, currentTime),
    [raceControlData, currentTime]
  );

  const seenKeysRef = useRef<Set<string>>(new Set());

  const [pulseKeys, setPulseKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    const nextPulse = new Set<string>();

    for (const msg of messages) {
      const key = raceControlKey(msg);
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
          <li className="p-4 pb-2 text-xs opacity-60 tracking-wide">
            Race Control
          </li>

          <AnimatePresence initial={false}>
            {messages.map((msg) => {
              const key = raceControlKey(msg);
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
                    {/* Time */}
                    <div className="text-xs uppercase font-semibold opacity-60">
                      {msg.time}
                    </div>

                    {/* Driver / Lap */}
                    <div className="text-xs font-semibold opacity-60">
                      {msg.driver_number != null
                        ? `Driver ${msg.driver_number} |`
                        : ""}
                      {msg.lap_number ? ` Lap ${msg.lap_number}` : ""}
                    </div>

                    {/* Message */}
                    <div>{msg.message}</div>
                  </div>

                  <div className="flex gap-2 items-center">
                    {msg.flag ? (
                      <div className="flex flex-col items-center leading-none">
                        <RaceControlFlag flag={msg.flag} className="w-6 h-6" />

                        <span className="mt-0.5 text-[10px] uppercase tracking-wide opacity-50">
                          {msg.flag}
                        </span>
                      </div>
                    ) : null}
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

function getRaceControlMessagesAtTime(
  raceControlData: RaceControlApiResponse[] | null,
  currentTime: number
): RaceControlApiResponse[] {
  if (!raceControlData?.length) return [];

  return raceControlData
    .filter((msg) => msg.SessionTime <= currentTime)
    .sort((a, b) => b.SessionTime - a.SessionTime); // newest first
}

// SessionTime+message+lap (to avoid duplicates)
function raceControlKey(msg: RaceControlApiResponse): string {
  return `${msg.SessionTime}-${msg.lap_number ?? "NA"}-${
    msg.driver_number ?? "RC"
  }-${msg.category ?? "NA"}-${msg.message}`;
}

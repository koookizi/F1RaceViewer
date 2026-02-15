import React, { useEffect, useMemo, useRef, useState } from "react";
import type { LeaderboardApiResponse, LeaderboardCarData } from "../types";
import { atOrBefore } from "../helpers/leaderboard";
import { getDriverFullNameByNumber } from "../helpers/driver_identifiers";
import { motion } from "framer-motion";
import { SpeedGauge } from "./SpeedGauge";
import { RpmGauge } from "./RPMGauge";
import { GearGauge } from "./GearGauge";

type RacePlaybackCarDataProps = {
    leaderboardData: LeaderboardApiResponse | null;
    currentTime: number;
    selectedDriver: number | null;
};

export function RacePlaybackCarData({
    leaderboardData,
    currentTime,
    selectedDriver,
}: RacePlaybackCarDataProps) {
    if (!leaderboardData) {
        return <div className="skeleton h-24 w-auto"></div>;
    }

    const carData = leaderboardData.drivers.find((d) => d.driver_number === selectedDriver) ?? null;

    const brake = getBrake(carData?.car_data, currentTime) ?? false;
    const throttle = getThrottle(carData?.car_data, currentTime) ?? 0;

    const isSelected = selectedDriver !== null;

    return (
        <div className="card card-border bg-base-100 w-full">
            <div className="card-body p-3 overflow-y-auto">
                {selectedDriver != null ? (
                    <>
                        <span className="text-xs opacity-60 tracking-wide">
                            {getDriverFullNameByNumber(leaderboardData, selectedDriver)}
                        </span>

                        <div className="flex items-center justify-center ps-3">
                            <SpeedGauge
                                carData={carData?.car_data ?? []}
                                currentTime={currentTime}
                                size={140}
                            />
                            <RpmGauge
                                carData={carData?.car_data ?? []}
                                currentTime={currentTime}
                                size={140}
                            />
                            <GearGauge
                                carData={carData?.car_data ?? []}
                                currentTime={currentTime}
                                size={140}
                            />
                        </div>

                        <dl className="flex flex-col gap-2 -mt-4">
                            <div className="flex items-center gap-3">
                                <dt className="w-20 text-[0.8em] opacity-70 whitespace-nowrap">
                                    THROTTLE (%)
                                </dt>
                                <dd className="flex-1">
                                    <ThrottleBar percent={throttle} />
                                </dd>
                            </div>

                            <div className="flex items-center gap-3">
                                <dt className="w-20 text-[0.8em] opacity-70 whitespace-nowrap">
                                    BRAKE
                                </dt>
                                <dd className="flex-1">
                                    <BrakeBar active={brake} />
                                </dd>
                            </div>
                        </dl>
                    </>
                ) : (
                    <div className="flex text-sm opacity-60 h-24 text-center justify-center items-center">
                        Select a driver
                    </div>
                )}
            </div>
        </div>
    );
}

export function getSpeed(
    carData: LeaderboardCarData[] | undefined,
    currentTime: number,
): number | null {
    const data = carData ?? [];
    if (data.length === 0) return null;

    if (currentTime < data[0].SessionTime) return 0;

    const row = atOrBefore(data, currentTime);
    return row?.Speed != null ? Math.round(row.Speed) : null;
}

function getGear(carData: LeaderboardCarData[] | undefined, currentTime: number): number | null {
    const data = carData ?? [];
    if (data.length === 0) return null;

    if (currentTime < data[0].SessionTime) return 0;

    const row = atOrBefore(data, currentTime);
    return row?.nGear != null ? row.nGear : null;
}

export function getRPM(
    carData: LeaderboardCarData[] | undefined,
    currentTime: number,
): number | null {
    const data = carData ?? [];
    if (data.length === 0) return null;

    if (currentTime < data[0].SessionTime) return 0;

    const row = atOrBefore(data, currentTime);
    return row?.RPM != null ? Math.round(row.RPM) : null;
}

function getBrake(carData: LeaderboardCarData[] | undefined, currentTime: number): boolean | null {
    const data = carData ?? [];
    if (data.length === 0) return null;

    if (currentTime < data[0].SessionTime) return null;

    const row = atOrBefore(data, currentTime);
    return row?.Brake != null ? row.Brake : null;
}

function getThrottle(
    carData: LeaderboardCarData[] | undefined,
    currentTime: number,
): number | null {
    const data = carData ?? [];
    if (data.length === 0) return null;

    if (currentTime < data[0].SessionTime) return 0;

    const row = atOrBefore(data, currentTime);
    return row?.Throttle != null ? row.Throttle : null;
}

function BrakeBar({ active }: { active: boolean }) {
    return (
        <div className="h-2 w-full rounded-full bg-base-300 overflow-hidden">
            <motion.div
                className="h-full w-full bg-error"
                // When off: invisible. When on: pulse.
                animate={active ? { opacity: [0.35, 1, 0.35] } : { opacity: 0 }}
                transition={
                    active
                        ? { duration: 0.8, repeat: Infinity, ease: "easeInOut" }
                        : { duration: 0.15 }
                }
            />
        </div>
    );
}

function ThrottleBar({ percent }: { percent: number }) {
    const clamped = Math.max(0, Math.min(100, percent));

    return (
        <div className="h-2 w-full rounded-full bg-base-300 overflow-hidden">
            <motion.div
                className="h-full bg-success"
                animate={{ width: `${clamped}%` }}
                transition={{ type: "spring", stiffness: 220, damping: 30 }}
            />
        </div>
    );
}

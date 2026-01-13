// src/components/VRTemplateInputs.tsx
import React, { useMemo } from "react";
import { MultiSelect } from "./MultiSelect";
import type { MultiSelectOption } from "./MultiSelect";
import type { Template } from "../helpers/templates";

export type LapPickMode = "Fastest" | "Manual";

export type VRTemplateInputsState = {
    // selection mode for templates that allow driver OR team
    selectionMode: "Drivers" | "Teams";

    // shared selectors
    driverIds: Array<string | number>;
    teamIds: Array<string | number>;

    // lap selection (telemetry)
    lapModeA: LapPickMode;
    lapNumberA: number | "";
    lapModeB: LapPickMode;
    lapNumberB: number | "";

    // ranges
    lapFrom: number | "";
    lapTo: number | "";

    // misc
    topN: number | "";
    season: number | "";

    // telemetry options
    telemetryAlign: "Distance" | "Time";
    telemetryChannels: Array<"Speed" | "Throttle" | "Brake" | "RPM" | "nGear" | "DRS" | "X/Y">;

    // common filters
    excludeSCLaps: boolean;
};

export const DEFAULT_VR_TEMPLATE_INPUTS: VRTemplateInputsState = {
    selectionMode: "Drivers",
    driverIds: [],
    teamIds: [],

    lapModeA: "Fastest",
    lapNumberA: "",
    lapModeB: "Fastest",
    lapNumberB: "",

    lapFrom: "",
    lapTo: "",

    topN: 10,
    season: new Date().getFullYear(),

    telemetryAlign: "Distance",
    telemetryChannels: ["Speed", "Throttle", "Brake"],

    excludeSCLaps: true,
};

type Props = {
    selectedTemplate: Template | null;

    driverOptions: MultiSelectOption[];
    teamOptions: MultiSelectOption[];

    value: VRTemplateInputsState;
    onChange: (next: VRTemplateInputsState) => void;

    className?: string;
};

export function VRTemplateInputs({
    selectedTemplate,
    driverOptions,
    teamOptions,
    value,
    onChange,
    className = "",
}: Props) {
    const templateId = selectedTemplate?.id ?? null;

    function patch(partial: Partial<VRTemplateInputsState>) {
        onChange({ ...value, ...partial });
    }

    const requires = useMemo(() => getRequirements(templateId), [templateId]);

    if (!selectedTemplate) {
        return (
            <div className={`mt-3 ${className}`}>
                <div className="alert alert-info">
                    <span className="text-sm">Select a template to see the required inputs.</span>
                </div>
            </div>
        );
    }

    return (
        <div className={`mt-3 space-y-3 ${className}`}>
            <div className="pb-1 text-xs opacity-60 tracking-wide">Required inputs</div>

            {/* Common filter (nice default for Pace/Strategy) */}
            {requires.showExcludeSC && (
                <label className="label cursor-pointer justify-start gap-3">
                    <input
                        type="checkbox"
                        className="toggle toggle-primary toggle-sm"
                        checked={value.excludeSCLaps}
                        onChange={(e) => patch({ excludeSCLaps: e.target.checked })}
                    />
                    <span className="label-text text-sm">Exclude SC/VSC laps</span>
                </label>
            )}

            {/* Choose whether template uses Drivers or Teams (for templates that allow either) */}
            {requires.allowDriverOrTeam && (
                <div className="join w-full">
                    <button
                        type="button"
                        className={`btn btn-sm join-item flex-1 ${
                            value.selectionMode === "Drivers" ? "btn-primary" : "btn-ghost"
                        }`}
                        onClick={() => patch({ selectionMode: "Drivers", teamIds: [] })}
                    >
                        Drivers
                    </button>
                    <button
                        type="button"
                        className={`btn btn-sm join-item flex-1 ${
                            value.selectionMode === "Teams" ? "btn-primary" : "btn-ghost"
                        }`}
                        onClick={() => patch({ selectionMode: "Teams", driverIds: [] })}
                    >
                        Teams
                    </button>
                </div>
            )}

            {/* Drivers */}
            {requires.drivers && value.selectionMode === "Drivers" && (
                <MultiSelect
                    options={driverOptions}
                    value={value.driverIds}
                    onChange={(ids) => patch({ driverIds: ids })}
                    placeholder={
                        requires.drivers.min === 1 && requires.drivers.max === 1
                            ? "Select driver"
                            : "Select driver(s)"
                    }
                    widthClassName="w-100"
                    maxChipsRows={2}
                />
            )}

            {/* Teams */}
            {requires.teams && value.selectionMode === "Teams" && (
                <MultiSelect
                    options={teamOptions}
                    value={value.teamIds}
                    onChange={(ids) => patch({ teamIds: ids })}
                    placeholder="Select team(s)"
                    widthClassName="w-100"
                    maxChipsRows={2}
                />
            )}

            {/* Lap Range (e.g., positions, battle analysis) */}
            {requires.lapRange && (
                <div className="grid grid-cols-2 gap-2 w-100">
                    <div className="form-control">
                        <label className="label py-1">
                            <span className="label-text text-sm">Lap from</span>
                        </label>
                        <input
                            type="number"
                            className="input input-sm input-bordered"
                            value={value.lapFrom}
                            onChange={(e) =>
                                patch({ lapFrom: e.target.value ? Number(e.target.value) : "" })
                            }
                            min={1}
                        />
                    </div>
                    <div className="form-control">
                        <label className="label py-1">
                            <span className="label-text text-sm">Lap to</span>
                        </label>
                        <input
                            type="number"
                            className="input input-sm input-bordered"
                            value={value.lapTo}
                            onChange={(e) =>
                                patch({ lapTo: e.target.value ? Number(e.target.value) : "" })
                            }
                            min={1}
                        />
                    </div>
                </div>
            )}

            {/* Top-N selector (positions filtered view) */}
            {requires.topN && (
                <div className="form-control w-100">
                    <label className="label py-1">
                        <span className="label-text text-sm me-2">Top N</span>
                    </label>
                    <input
                        type="number"
                        className="input input-sm input-bordered w-30"
                        value={value.topN}
                        onChange={(e) =>
                            patch({ topN: e.target.value ? Number(e.target.value) : "" })
                        }
                        min={1}
                        max={30}
                    />
                </div>
            )}

            {/* Season selector (season intent) */}
            {requires.season && (
                <div className="form-control w-100">
                    <label className="label py-1">
                        <span className="label-text text-sm me-2">Season</span>
                    </label>
                    <input
                        type="number"
                        className="input input-sm input-bordered w-20"
                        value={value.season}
                        onChange={(e) =>
                            patch({ season: e.target.value ? Number(e.target.value) : "" })
                        }
                        min={1950}
                        max={2100}
                    />
                </div>
            )}

            {/* Telemetry compare (needs 2 laps) */}
            {requires.telemetryCompare && (
                <div className="space-y-2">
                    <div className="divider my-1">Lap selection</div>

                    <div className="alert alert-warning my-4">
                        <span className="text-sm">
                            Pick 1-2 drivers. If two drivers are selected, the chart compares their
                            chosen laps. If one driver is selected, compare two laps from the same
                            driver.
                        </span>
                    </div>

                    {/* Driver selection (max 2 recommended) */}
                    <MultiSelect
                        options={driverOptions}
                        value={value.driverIds}
                        onChange={(ids) => patch({ driverIds: ids })}
                        placeholder="Select 1-2 drivers"
                        widthClassName="w-100"
                        maxChipsRows={2}
                    />

                    <div className="grid grid-cols-2 gap-2 w-100 mb-4">
                        <div className="form-control">
                            <label className="label py-1">
                                <span className="label-text text-sm">Lap A</span>
                            </label>
                            <select
                                className="select select-sm select-bordered"
                                value={value.lapModeA}
                                onChange={(e) => patch({ lapModeA: e.target.value as LapPickMode })}
                            >
                                <option value="Fastest">Fastest lap</option>
                                <option value="Manual">Manual lap number</option>
                            </select>
                            {value.lapModeA === "Manual" && (
                                <input
                                    type="number"
                                    className="input input-sm input-bordered mt-2"
                                    placeholder="Lap number"
                                    value={value.lapNumberA}
                                    onChange={(e) =>
                                        patch({
                                            lapNumberA: e.target.value
                                                ? Number(e.target.value)
                                                : "",
                                        })
                                    }
                                    min={1}
                                />
                            )}
                        </div>

                        <div className="form-control">
                            <label className="label py-1">
                                <span className="label-text text-sm">Lap B</span>
                            </label>
                            <select
                                className="select select-sm select-bordered"
                                value={value.lapModeB}
                                onChange={(e) => patch({ lapModeB: e.target.value as LapPickMode })}
                            >
                                <option value="Fastest">Fastest lap</option>
                                <option value="Manual">Manual lap number</option>
                            </select>
                            {value.lapModeB === "Manual" && (
                                <input
                                    type="number"
                                    className="input input-sm input-bordered mt-2"
                                    placeholder="Lap number"
                                    value={value.lapNumberB}
                                    onChange={(e) =>
                                        patch({
                                            lapNumberB: e.target.value
                                                ? Number(e.target.value)
                                                : "",
                                        })
                                    }
                                    min={1}
                                />
                            )}
                        </div>
                    </div>

                    <div className="divider my-4">Telemetry options</div>

                    <div className="form-control w-100 mb-4">
                        <label className="label py-1">
                            <span className="label-text text-sm me-2">Align by</span>
                        </label>
                        <select
                            className="select select-sm select-bordered w-30"
                            value={value.telemetryAlign}
                            onChange={(e) =>
                                patch({ telemetryAlign: e.target.value as "Distance" | "Time" })
                            }
                        >
                            <option value="Distance">Distance</option>
                            <option value="Time">Time</option>
                        </select>
                    </div>

                    <MultiSelect
                        options={[
                            { id: "Speed", label: "Speed" },
                            { id: "Throttle", label: "Throttle" },
                            { id: "Brake", label: "Brake" },
                            { id: "RPM", label: "RPM" },
                            { id: "nGear", label: "nGear" },
                            { id: "DRS", label: "DRS" },
                            { id: "X/Y", label: "X/Y (track map)" },
                        ]}
                        value={value.telemetryChannels}
                        onChange={(ids) =>
                            patch({
                                telemetryChannels:
                                    ids as VRTemplateInputsState["telemetryChannels"],
                            })
                        }
                        placeholder="Select telemetry channels"
                        widthClassName="w-100"
                        maxChipsRows={2}
                    />
                </div>
            )}

            {/* Simple single-lap telemetry (track map / gear map etc.) */}
            {requires.telemetrySingleLap && (
                <div className="space-y-2">
                    <div className="divider mb-4">Lap selection</div>

                    <MultiSelect
                        options={driverOptions}
                        value={value.driverIds}
                        onChange={(ids) => patch({ driverIds: ids })}
                        placeholder="Select driver"
                        widthClassName="w-100"
                        maxChipsRows={1}
                    />

                    <div className="form-control w-100 mt-4">
                        <label className="label py-1">
                            <span className="label-text text-sm">Lap</span>
                        </label>
                        <select
                            className="select select-sm select-bordered"
                            value={value.lapModeA}
                            onChange={(e) => patch({ lapModeA: e.target.value as LapPickMode })}
                        >
                            <option value="Fastest">Fastest lap</option>
                            <option value="Manual">Manual lap number</option>
                        </select>

                        {value.lapModeA === "Manual" && (
                            <input
                                type="number"
                                className="input input-sm input-bordered mt-2"
                                placeholder="Lap number"
                                value={value.lapNumberA}
                                onChange={(e) =>
                                    patch({
                                        lapNumberA: e.target.value ? Number(e.target.value) : "",
                                    })
                                }
                                min={1}
                            />
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

/**
 * Minimal requirements mapping per template id.
 * Keep this in sync with your TEMPLATES ids (t1..t23).
 */
function getRequirements(templateId: string | null) {
    // Default: nothing
    const base = {
        showExcludeSC: false,
        allowDriverOrTeam: false,
        drivers: null as null | { min: number; max?: number },
        teams: null as null | { min: number; max?: number },
        lapRange: false,
        topN: false,
        season: false,
        telemetryCompare: false,
        telemetrySingleLap: false,
    };

    if (!templateId) return base;

    // Pace
    if (["t1", "t2", "t3", "t4", "t5"].includes(templateId)) {
        return {
            ...base,
            showExcludeSC: true,
            allowDriverOrTeam: false,
            drivers: { min: 1 },
        };
    }
    if (templateId === "t6") {
        return {
            ...base,
            showExcludeSC: true,
            allowDriverOrTeam: false,
            teams: { min: 1 },
        };
    }

    // Strategy (driver OR team)
    if (["t7", "t8", "t9", "t10", "t11"].includes(templateId)) {
        return {
            ...base,
            showExcludeSC: true,
            allowDriverOrTeam: true,
            drivers: { min: 1 },
            teams: { min: 1 },
        };
    }

    // Telemetry
    if (templateId === "t12" || templateId === "t13") {
        return {
            ...base,
            telemetryCompare: true,
        };
    }
    if (["t14", "t15", "t16"].includes(templateId)) {
        return {
            ...base,
            telemetrySingleLap: true,
        };
    }
    if (templateId === "t17") {
        return {
            ...base,
            drivers: { min: 1, max: 1 },
            lapRange: true,
        };
    }

    // Positions
    if (templateId === "t18") {
        return {
            ...base,
            drivers: { min: 1 },
            lapRange: false,
        };
    }
    if (templateId === "t19") {
        return {
            ...base,
            drivers: { min: 1, max: 1 },
        };
    }
    if (templateId === "t20") {
        return {
            ...base,
            topN: true,
        };
    }

    // Season
    if (templateId === "t21" || templateId === "t22" || templateId === "t23") {
        return {
            ...base,
            season: true,
        };
    }

    return base;
}

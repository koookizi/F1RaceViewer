import React, { useEffect, useMemo, useState } from "react";
import type { MultiSelectOption } from "./MultiSelect";
import { TemplateCardPanel } from "./TemplateCardPanel";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import { TEMPLATES, type Intent, type Page } from "../helpers/templates";
import { VRTemplateInputs, DEFAULT_VR_TEMPLATE_INPUTS } from "./VRTemplateInputs";
import type { ChartResponse } from "./ChartCard";
import { useToast } from "./ToastContext";

type VRBuilderBuildControlsProps = {
    DRIVER_OPTIONS?: MultiSelectOption[];
    TEAM_OPTIONS?: MultiSelectOption[];
    selectedYear?: string;
    selectedCountry?: string;
    selectedSession?: string;
    selectedTeam?: string;
    selectedDriverCode?: string;
    setChartLoading: React.Dispatch<React.SetStateAction<boolean>>;
    setPreviewChart: React.Dispatch<React.SetStateAction<ChartResponse | null>>;
    chartLoading: boolean;
    page: Page;
};

/**
 * Provides controls for configuring and generating visualisations.
 *
 * Handles template selection, input submission and triggering backend
 * requests to build the selected visualisation.
 */
export function VRBuilderBuildControls({
    page,
    DRIVER_OPTIONS = [],
    TEAM_OPTIONS = [],
    selectedYear = "",
    selectedCountry = "",
    selectedSession = "",
    selectedTeam = "",
    selectedDriverCode = "",
    setPreviewChart,
    setChartLoading,
    chartLoading,
}: VRBuilderBuildControlsProps) {
    useEffect(() => {
        setSelectedIntent("");
        setSelectedTemplateId(null);
    }, [page]);

    const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

    const [selectedIntent, setSelectedIntent] = useState<Intent | "">("");

    const templatesForPage = useMemo(() => {
        return TEMPLATES.filter((t) => t.page === page);
    }, [page]);

    const intentsForPage = useMemo(() => {
        return Array.from(new Set(templatesForPage.map((t) => t.intent)));
    }, [templatesForPage]);

    const templatesForIntent = useMemo(() => {
        if (!selectedIntent) return [];
        return templatesForPage.filter((t) => t.intent === selectedIntent);
    }, [templatesForPage, selectedIntent]);

    const selectedTemplate = useMemo(() => {
        return templatesForPage.find((t) => t.id === selectedTemplateId) ?? null;
    }, [templatesForPage, selectedTemplateId]);

    const toast = useToast();

    const [inputs, setInputs] = useState(DEFAULT_VR_TEMPLATE_INPUTS);

    useEffect(() => {
        console.log(selectedTemplateId);
    }, [selectedTemplateId]);

    function validateInputs(templateId: string): string[] {
        const errors: string[] = [];

        // requires >= 1 driver(s)
        if (["t1", "t2", "t3", "t4", "t5", "t18"].includes(templateId)) {
            if (inputs.driverIds.length < 1) errors.push("Select at least 1 driver.");
        }

        // requires >=1 team(s)
        if (templateId === "t6") {
            if (inputs.teamIds.length < 1) errors.push("Select at least 1 team.");
        }

        // requires atleast 1 driver OR atleast 1 team
        if (["t7", "t8", "t9", "t10", "t11"].includes(templateId)) {
            if (inputs.selectionMode == "Drivers") {
                if (inputs.driverIds.length < 1) errors.push("Select at least 1 driver.");
            } else if (inputs.selectionMode == "Teams") {
                if (inputs.teamIds.length < 1) errors.push("Select at least 1 team.");
            }
        }

        // requires 1 or 2 drivers, lap modes/numbers, telemetry channels
        if (templateId === "t12" || templateId === "t13") {
            if (inputs.driverIds.length < 1) errors.push("Select at least 1 driver.");
            if (inputs.driverIds.length > 2) errors.push("Select at most 2 drivers.");
            if (inputs.lapModeA === "Manual" && inputs.lapNumberA === "")
                errors.push("Lap A number is required (Manual).");
            if (inputs.lapModeB === "Manual" && inputs.lapNumberB === "")
                errors.push("Lap B number is required (Manual).");
            if (inputs.telemetryChannels.length < 1)
                errors.push("Select at least 1 telemetry channel.");
        }

        // requires 1 driver, lap mode/number
        if (["t14", "t15", "t16"].includes(templateId)) {
            if (inputs.lapModeA === "Manual" && inputs.lapNumberA === "")
                errors.push("Lap A number is required (Manual).");
            if (inputs.driverIds.length != 1) errors.push("Select a driver.");
        }

        // requires 1 driver, lap from/to
        if (["t17"].includes(templateId)) {
            if (inputs.driverIds.length != 1) errors.push("Select a driver.");
            if (inputs.lapFrom == "") errors.push("Enter a 'Lap from'.");
            if (inputs.lapTo == "") errors.push("Enter a 'Lap to'.");
        }

        // requires exactly 1 driver
        if (["t19"].includes(templateId)) {
            if (inputs.driverIds.length != 1) errors.push("Select a driver.");
        }

        // requires top N > 0
        if (["t20"].includes(templateId)) {
            if (inputs.topN == 0) errors.push("Enter a number.");
        }

        // requires season
        if (
            [
                "t21",
                "t22",
                "t24",
                "t25",
                "t26",
                "t30",
                "t31",
                "t32",
                "t33",
                "t34",
                "t35",
                "t36",
                "t37",
                "t38",
                "t39",
                "t40",
            ].includes(templateId)
        ) {
            if (inputs.season == 0) errors.push("Enter a season.");
        }

        // requires season and round
        if (["t23"].includes(templateId)) {
            if (inputs.season == 0) errors.push("Enter a season.");
            if (inputs.round == 0) errors.push("Enter a round.");
        }

        // requires season range
        if (["t27", "t28", "t29"].includes(templateId)) {
            if (inputs.seasonFrom == 0) errors.push("Enter a season from.");
            if (inputs.seasonTo == 0) errors.push("Enter a season to.");
        }

        return errors;
    }

    function buildPayload(templateId: string) {
        const base = {
            excludeSCLaps: inputs.excludeSCLaps,
        };

        const drivers = inputs.driverIds.map(String);
        const teams = inputs.teamIds.map(String);

        // requires >= 1 driver(s)
        if (["t1", "t2", "t3", "t4", "t5", "t18", "t19"].includes(templateId)) {
            return {
                ...base,
                drivers,
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        // requires >=1 team(s)
        if (templateId === "t6") {
            return {
                ...base,
                teams,
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        // requires 1 or 2 drivers, lap modes/numbers, telemetry channels
        if (templateId === "t12" || templateId === "t13") {
            const lapA = inputs.lapModeA === "Fastest" ? "fastest" : inputs.lapNumberA;
            const lapB = inputs.lapModeB === "Fastest" ? "fastest" : inputs.lapNumberB;

            return {
                ...base,
                drivers,
                lapA,
                lapB,
                align: inputs.telemetryAlign,
                channels: inputs.telemetryChannels,
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        // requires 1 driver, lap mode/number
        if (["t14", "t15", "t16"].includes(templateId)) {
            const lap = inputs.lapModeA === "Fastest" ? "fastest" : inputs.lapNumberA;

            // if backend expects ONE driver, then drivers[0]
            return {
                ...base,
                drivers, // or driver: drivers[0]
                lap, // "fastest" | number | ""
                align: inputs.telemetryAlign,
                channels: inputs.telemetryChannels,
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        // requires 1 driver, lap from/to
        if (templateId === "t17") {
            return {
                ...base,
                drivers, // or driver: drivers[0]
                lapFrom: inputs.lapFrom, // number | ""
                lapTo: inputs.lapTo, // number | ""
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        // requires top N > 0
        if (templateId === "t20") {
            return {
                ...base,
                topN: inputs.topN, // number | ""
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        // requires season
        if (["t21", "t22"].includes(templateId)) {
            return {
                ...base,
                season: inputs.season, // number | ""
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        // requires season (team)
        if (["t24", "t25", "t26", "t30", "t31"].includes(templateId)) {
            return {
                ...base,
                season: inputs.season, // number | ""
                team: selectedTeam,
            };
        }

        // requires season (driver)
        if (["t32", "t33", "t34", "t35", "t36", "t37", "t38", "t39", "t40"].includes(templateId)) {
            return {
                ...base,
                season: inputs.season, // number | ""
                driver: selectedDriverCode,
            };
        }

        // requires season range (team)
        if (["t27", "t28", "t29"].includes(templateId)) {
            return {
                ...base,
                seasonFrom: inputs.seasonFrom,
                seasonTo: inputs.seasonTo,
                team: selectedTeam,
            };
        }

        // requires season and round
        if (templateId === "t23") {
            return {
                ...base,
                season: inputs.season, // number | ""
                round: inputs.round, // number | ""
                year: selectedYear,
                country: selectedCountry,
                session_name: selectedSession,
            };
        }

        return base;
    }

    function onCreate() {
        if (!selectedTemplate) return;

        const errors = validateInputs(selectedTemplate.id);
        if (errors.length) {
            toast(errors.join("\n"), "error");
            return;
        }

        const body = {
            templateId: selectedTemplate.id,
            inputs: buildPayload(selectedTemplate.id),
        };

        setChartLoading(true);
        fetch("/api/session/vr/create/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        })
            .then(async (res) => {
                if (!res.ok) throw new Error(await res.text());
                return res.json();
            })
            .then((result) => {
                const inputsSnapshot = buildPayload(selectedTemplate.id);

                setPreviewChart({
                    ...result,
                    meta: {
                        ...(result.meta ?? {}),
                        createdAtISO: new Date().toISOString(),
                        templateId: selectedTemplate.id,
                        intent: selectedIntent || undefined,
                        year: selectedYear,
                        country: selectedCountry,
                        session_name: selectedSession,
                        inputs: inputsSnapshot,
                    },
                });

                setChartLoading(false);
            })
            .catch((err) => console.error("Create failed:", err))
            .finally(() => setChartLoading(false));
    }

    return (
        <div className="card card-border bg-base-100 w-full">
            <div className="card-body p-4 h-140 overflow-y-auto">
                <div className="pb-2 text-xs opacity-60 tracking-wide flex items-center">
                    <span>Builder</span>
                </div>

                {/* Intent dropdown */}
                <div className="dropdown">
                    <div tabIndex={0} role="button" className="btn flex items-center gap-2 w-70">
                        {selectedIntent || "Select Intent"}
                        <ChevronDownIcon aria-hidden="true" className="size-5 opacity-70" />
                    </div>

                    <ul
                        tabIndex={0}
                        className="dropdown-content menu bg-base-100 rounded-box z-10 w-56 shadow max-h-96 overflow-y-auto"
                    >
                        {intentsForPage.map((intent) => (
                            <li key={intent}>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setSelectedIntent(intent);
                                        setSelectedTemplateId(null);
                                    }}
                                >
                                    {intent}
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Templates list (filtered by intent) */}
                <TemplateCardPanel
                    intent={selectedIntent}
                    templates={templatesForIntent}
                    selectedTemplateId={selectedTemplateId}
                    onSelectTemplate={(t) => setSelectedTemplateId(t.id)}
                    heightClassName="h-80"
                />

                <VRTemplateInputs
                    selectedTemplate={selectedTemplate}
                    driverOptions={DRIVER_OPTIONS}
                    teamOptions={TEAM_OPTIONS}
                    value={inputs}
                    onChange={setInputs}
                />

                <button
                    className="btn btn-primary mt-4"
                    onClick={onCreate}
                    disabled={!selectedTemplate || chartLoading}
                >
                    Create
                </button>
            </div>
        </div>
    );
}

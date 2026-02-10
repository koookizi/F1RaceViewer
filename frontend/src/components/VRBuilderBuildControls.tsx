// VRBuilderBuildControls.tsx
import React, { useEffect, useMemo, useState } from "react";
import type { MultiSelectOption } from "./MultiSelect";
import { TemplateCardPanel } from "./TemplateCardPanel";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import { TEMPLATES, type Intent } from "../helpers/templates";
import { VRTemplateInputs, DEFAULT_VR_TEMPLATE_INPUTS } from "./VRTemplateInputs";
import type { ChartResponse } from "./ChartCard";
import { useToast } from "./ToastContext";

const INTENTS: Intent[] = ["Pace", "Strategy", "Telemetry", "Positions", "Season"];

type VRBuilderBuildControlsProps = {
    DRIVER_OPTIONS: MultiSelectOption[];
    TEAM_OPTIONS: MultiSelectOption[];
    selectedYear: string;
    selectedCountry: string;
    selectedSession: string;
    setChartLoading: React.Dispatch<React.SetStateAction<boolean>>;
    setPreviewChart: React.Dispatch<React.SetStateAction<ChartResponse | null>>;
    chartLoading: boolean;
};

export function VRBuilderBuildControls({
    DRIVER_OPTIONS,
    TEAM_OPTIONS,
    selectedYear,
    selectedCountry,
    selectedSession,
    setPreviewChart,
    setChartLoading,
    chartLoading,
}: VRBuilderBuildControlsProps) {
    const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

    const [selectedIntent, setSelectedIntent] = useState<Intent | "">("");

    const templatesForIntent = useMemo(() => {
        if (!selectedIntent) return [];
        return TEMPLATES.filter((t) => t.intent === selectedIntent);
    }, [selectedIntent]);

    const selectedTemplate = useMemo(
        () => TEMPLATES.find((t) => t.id === selectedTemplateId) ?? null,
        [selectedTemplateId],
    );

    const toast = useToast();

    const [inputs, setInputs] = useState(DEFAULT_VR_TEMPLATE_INPUTS);

    useEffect(() => {
        console.log(selectedTemplateId);
    }, [selectedTemplateId]);

    function validateInputs(templateId: string): string[] {
        const errors: string[] = [];

        // Requires >= 1 driver(s)
        if (["t1", "t2", "t3", "t4", "t5", "t18"].includes(templateId)) {
            if (inputs.driverIds.length < 1) errors.push("Select at least 1 driver.");
        }

        // Requires >=1 team(s)
        if (templateId === "t6") {
            if (inputs.teamIds.length < 1) errors.push("Select at least 1 team.");
        }

        // Requires atleast 1 driver OR atleast 1 team
        if (["t7", "t8", "t9", "t10", "t11"].includes(templateId)) {
            if (inputs.selectionMode == "Drivers") {
                if (inputs.driverIds.length < 1) errors.push("Select at least 1 driver.");
            } else if (inputs.selectionMode == "Teams") {
                if (inputs.teamIds.length < 1) errors.push("Select at least 1 team.");
            }
        }

        // Rquires 1 or 2 drivers, lap modes/numbers, telemetry channels
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

        // Requires 1 driver, lap mode/number
        if (["t14", "t15", "t16"].includes(templateId)) {
            if (inputs.lapModeA === "Manual" && inputs.lapNumberA === "")
                errors.push("Lap A number is required (Manual).");
            if (inputs.driverIds.length != 1) errors.push("Select a driver.");
        }

        // Requires 1 driver, lap from/to
        if (["t17"].includes(templateId)) {
            if (inputs.driverIds.length != 1) errors.push("Select a driver.");
            if (inputs.lapFrom == "") errors.push("Enter a 'Lap from'.");
            if (inputs.lapTo == "") errors.push("Enter a 'Lap to'.");
        }

        // Requires exactly 1 driver
        if (["t19"].includes(templateId)) {
            if (inputs.driverIds.length != 1) errors.push("Select a driver.");
        }

        // Requires top N > 0
        if (["t20"].includes(templateId)) {
            if (inputs.topN == 0) errors.push("Enter a number.");
        }

        // Requires season
        if (["t21", "t22"].includes(templateId)) {
            if (inputs.season == 0) errors.push("Enter a season.");
        }

        // Requires season and round
        if (["t23"].includes(templateId)) {
            if (inputs.season == 0) errors.push("Enter a season.");
            if (inputs.round == 0) errors.push("Enter a round.");
        }

        return errors;
    }

    function buildPayload(templateId: string) {
        const base = {
            excludeSCLaps: inputs.excludeSCLaps,
        };

        const drivers = inputs.driverIds.map(String);
        const teams = inputs.teamIds.map(String);

        // Requires >= 1 driver(s)
        if (["t1", "t2", "t3", "t4", "t5", "t18", "t19"].includes(templateId)) {
            return {
                ...base,
                drivers,
            };
        }

        // Requires >=1 team(s)
        if (templateId === "t6") {
            return {
                ...base,
                teams,
            };
        }

        // Requires 1 or 2 drivers, lap modes/numbers, telemetry channels
        if (templateId === "t12" || templateId === "t13") {
            const lapA = inputs.lapModeA === "Fastest" ? "fastest" : inputs.lapNumberA;
            const lapB = inputs.lapModeB === "Fastest" ? "fastest" : inputs.lapNumberB;

            return {
                ...base,
                drivers,
                lapA, // "fastest" | number | ""
                lapB, // "fastest" | number | ""
                align: inputs.telemetryAlign,
                channels: inputs.telemetryChannels,
            };
        }

        // Requires 1 driver, lap mode/number
        if (["t14", "t15", "t16"].includes(templateId)) {
            const lap = inputs.lapModeA === "Fastest" ? "fastest" : inputs.lapNumberA;

            // if backend expects ONE driver, you may want drivers[0]
            return {
                ...base,
                drivers, // or driver: drivers[0]
                lap, // "fastest" | number | ""
                align: inputs.telemetryAlign,
                channels: inputs.telemetryChannels,
            };
        }

        // Requires 1 driver, lap from/to
        if (templateId === "t17") {
            return {
                ...base,
                drivers, // or driver: drivers[0]
                lapFrom: inputs.lapFrom, // number | ""
                lapTo: inputs.lapTo, // number | ""
            };
        }

        // Requires top N > 0
        if (templateId === "t20") {
            return {
                ...base,
                topN: inputs.topN, // number | ""
            };
        }

        // Requires season
        if (["t21", "t22"].includes(templateId)) {
            return {
                ...base,
                season: inputs.season, // number | ""
            };
        }

        // Requires season and round
        if (templateId === "t23") {
            return {
                ...base,
                season: inputs.season, // number | ""
                round: inputs.round, // number | ""
            };
        }

        return base;
    }

    function onCreate() {
        if (!selectedTemplate) return;

        // 1) validate
        const errors = validateInputs(selectedTemplate.id);
        if (errors.length) {
            toast(errors.join("\n"), "error");
            return;
        }

        const body = {
            templateId: selectedTemplate.id,
            year: selectedYear,
            country: selectedCountry,
            session_name: selectedSession, // match your Django param naming
            inputs: buildPayload(selectedTemplate.id),
        };

        setChartLoading(true);
        fetch("http://localhost:8000/api/session/vr/create/", {
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
                    <span>Builder</span>
                </div>

                {/* Intent dropdown */}
                <div className="dropdown">
                    <div tabIndex={0} role="button" className="btn flex items-center gap-2 w-40">
                        {selectedIntent || "Select Intent"}
                        <ChevronDownIcon aria-hidden="true" className="size-5 opacity-70" />
                    </div>

                    <ul
                        tabIndex={0}
                        className="dropdown-content menu bg-base-100 rounded-box z-10 w-56 shadow max-h-96 overflow-y-auto"
                    >
                        {INTENTS.map((intent) => (
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

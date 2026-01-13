// VRBuilderBuildControls.tsx
import React, { useEffect, useMemo, useState } from "react";
import type { MultiSelectOption } from "./MultiSelect";
import { TemplateCardPanel } from "./TemplateCardPanel";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import { TEMPLATES, type Intent } from "../helpers/templates";
import {
  VRTemplateInputs,
  DEFAULT_VR_TEMPLATE_INPUTS,
} from "./VRTemplateInputs";

const INTENTS: Intent[] = [
  "Pace",
  "Strategy",
  "Telemetry",
  "Positions",
  "Season",
];

type VRBuilderBuildControlsProps = {
  DRIVER_OPTIONS: MultiSelectOption[];
  TEAM_OPTIONS: MultiSelectOption[];
};

export function VRBuilderBuildControls({
  DRIVER_OPTIONS,
  TEAM_OPTIONS,
}: VRBuilderBuildControlsProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(
    null
  );

  const [selectedIntent, setSelectedIntent] = useState<Intent | "">("");

  const templatesForIntent = useMemo(() => {
    if (!selectedIntent) return [];
    return TEMPLATES.filter((t) => t.intent === selectedIntent);
  }, [selectedIntent]);

  const selectedTemplate = useMemo(
    () => TEMPLATES.find((t) => t.id === selectedTemplateId) ?? null,
    [selectedTemplateId]
  );

  const [inputs, setInputs] = useState(DEFAULT_VR_TEMPLATE_INPUTS);

  useEffect(() => {
    console.log(selectedTemplateId);
  }, [selectedTemplateId]);

  function validateInputs(templateId: string): string[] {
    const errors: string[] = [];

    // Pace templates t1..t5 require >=1 driver
    if (["t1", "t2", "t3", "t4", "t5", "t18"].includes(templateId)) {
      if (inputs.driverIds.length < 1) errors.push("Select at least 1 driver.");
    }

    // Team pace t6 requires >=1 team
    if (templateId === "t6") {
      if (inputs.teamIds.length < 1) errors.push("Select at least 1 team.");
    }

    if (["t7", "t8", "t9", "t10", "t11"].includes(templateId)) {
      if (inputs.selectionMode == "Drivers") {
        if (inputs.driverIds.length < 1)
          errors.push("Select at least 1 driver.");
      } else if (inputs.selectionMode == "Teams") {
        if (inputs.teamIds.length < 1) errors.push("Select at least 1 team.");
      }
    }

    // Telemetry compare t12/t13 require 1-2 drivers
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

    if (["t14", "t15", "t16"].includes(templateId)) {
      if (inputs.lapModeA === "Manual" && inputs.lapNumberA === "")
        errors.push("Lap A number is required (Manual).");
      if (inputs.driverIds.length != 1) errors.push("Select a driver.");
    }

    if (["t17"].includes(templateId)) {
      if (inputs.driverIds.length != 1) errors.push("Select a driver.");
      if (inputs.lapFrom == "") errors.push("Enter a 'Lap from'.");
      if (inputs.lapTo == "") errors.push("Enter a 'Lap to'.");
    }

    if (["t19"].includes(templateId)) {
      if (inputs.driverIds.length != 1) errors.push("Select a driver.");
    }

    if (["t20"].includes(templateId)) {
      if (inputs.topN == 0) errors.push("Enter a number.");
    }

    return errors;
  }

  function buildPayload(templateId: string) {
    // Start with common bits
    const base = {
      excludeSCLaps: inputs.excludeSCLaps,
    };

    // Example mapping by template type
    if (["t1", "t2", "t3", "t4", "t5"].includes(templateId)) {
      return {
        ...base,
        drivers: inputs.driverIds, // ["VER", "HAM"]
      };
    }

    if (templateId === "t6") {
      return {
        ...base,
        teams: inputs.teamIds, // ["Red Bull Racing"]
      };
    }

    if (templateId === "t12" || templateId === "t13") {
      return {
        ...base,
        drivers: inputs.driverIds,
        lapA: inputs.lapModeA === "Fastest" ? "fastest" : inputs.lapNumberA,
        lapB: inputs.lapModeB === "Fastest" ? "fastest" : inputs.lapNumberB,
        align: inputs.telemetryAlign, // "Distance" | "Time"
        channels: inputs.telemetryChannels, // ["Speed","Throttle",...]
      };
    }

    // fallback
    return base;
  }

  function onCreate() {
    if (!selectedTemplate) return;

    // 1) validate
    const errors = validateInputs(selectedTemplate.id);
    if (errors.length) {
      alert(errors.join("\n"));
      return;
    }

    // 2) build payload
    const payload = buildPayload(selectedTemplate.id);

    // 3) do something (call backend / create chart / add to report)
    console.log("CREATE:", { templateId: selectedTemplate.id, payload });

    // Example: call backend to generate data for chart
    fetch("http://localhost:8000/api/vr/render/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ templateId: selectedTemplate.id, ...payload }),
    })
      .then((r) => r.json())
      .then((data) => console.log("rendered data:", data))
      .catch(console.error);
  }

  return (
    <div className="card card-border bg-base-100 w-full">
      <div className="card-body p-4 h-140 overflow-y-auto">
        <div className="pb-2 text-xs opacity-60 tracking-wide flex items-center">
          <span>Build Controls</span>
        </div>

        {/* Intent dropdown */}
        <div className="dropdown">
          <div
            tabIndex={0}
            role="button"
            className="btn flex items-center gap-2 w-40"
          >
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
                    // reset template selection when intent changes
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

        <button className="btn btn-primary mt-4" onClick={onCreate}>
          Create
        </button>
      </div>
    </div>
  );
}

// VRBuilderBuildControls.tsx
import React, { useMemo, useState } from "react";
import { MultiSelect } from "./MultiSelect";
import type { MultiSelectOption } from "./MultiSelect";
import { TemplateCardPanel } from "./TemplateCardPanel";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import { TEMPLATES, type Intent } from "../helpers/templates";
import {
  VRTemplateInputs,
  DEFAULT_VR_TEMPLATE_INPUTS,
} from "./VRTemplateInputs";

const DRIVER_OPTIONS: MultiSelectOption[] = [
  { id: "VER", label: "VER" },
  { id: "HAM", label: "HAM" },
  { id: "NOR", label: "NOR" },
  { id: "LEC", label: "LEC" },
];

const TEAM_OPTIONS: MultiSelectOption[] = [
  { id: "Mercedes", label: "Mercedes" },
  { id: "Ferrari", label: "Ferrari" },
  { id: "Williams", label: "Williams" },
  { id: "Audi", label: "Audi" },
];

const INTENTS: Intent[] = [
  "Pace",
  "Strategy",
  "Telemetry",
  "Positions",
  "Season",
];

type VRBuilderBuildControlsProps = {};

export function VRBuilderBuildControls({}: VRBuilderBuildControlsProps) {
  const [VRSelectedDrivers, setVRSelectedDrivers] = useState<
    Array<string | number>
  >([]);

  const [VRSelectedTeams, setVRSelectedTeams] = useState<
    Array<string | number>
  >([]);

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

        {/* <pre className="mt-3 text-xs opacity-70">
          {JSON.stringify(VRSelectedDrivers, null, 2)}
        </pre> */}
      </div>
    </div>
  );
}

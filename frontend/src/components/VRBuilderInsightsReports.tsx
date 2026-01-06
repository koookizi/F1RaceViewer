import React, { useEffect, useMemo, useRef, useState } from "react";
import type { RaceControlApiResponse } from "../types";
import { AnimatePresence, motion } from "framer-motion";
import { RaceControlFlag } from "./RaceControlFlag";

type VRBuilderInsightsReportsProps = {};

export function VRBuilderInsightsReports({}: VRBuilderInsightsReportsProps) {
  return (
    <div className="card card-border bg-base-100 w-full">
      <div className="card-body p-4 h-40 overflow-y-auto">
        <div className="pb-2 text-xs opacity-60 tracking-wide flex items-center">
          <span>Insights and Reports</span>
        </div>
      </div>
    </div>
  );
}

import React, { useEffect, useMemo, useRef, useState } from "react";
import type { RaceControlApiResponse } from "../types";
import { AnimatePresence, motion } from "framer-motion";
import { RaceControlFlag } from "./RaceControlFlag";

import { ReportBlocksStrip } from "./ReportsBlocksStrip";
import { type ChartResponse } from "./ChartCard";

type VRBuilderInsightsReportsProps = {
    reportBlocks: ChartResponse[];
    setReportBlocks: React.Dispatch<React.SetStateAction<ChartResponse[]>>;
};

export function VRBuilderInsightsReports({
    reportBlocks,
    setReportBlocks,
}: VRBuilderInsightsReportsProps) {
    return (
        <div className="card card-border bg-base-100 w-full">
            <div className="card-body p-4 h-60 overflow-y-auto">
                <div className="pb-2 text-xs opacity-60 tracking-wide flex items-center">
                    <span>Insights and Reports</span>
                </div>
                <div
                    className={[
                        "rounded-xl border",
                        "bg-base-200 border-base-300/50",
                        "shadow-sm",
                    ].join(" ")}
                >
                    <div className="px-4 pt-4 pb-2 flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="text-xs opacity-70">
                                Current Report
                            </span>
                        </div>
                    </div>

                    <div className={`px-4 pb-4`}>
                        <ReportBlocksStrip
                            reportBlocks={reportBlocks}
                            onRemove={(index) =>
                                setReportBlocks((prev) =>
                                    prev.filter((_, i) => i !== index)
                                )
                            }
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

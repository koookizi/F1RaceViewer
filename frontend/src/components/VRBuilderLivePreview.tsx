import React, { useEffect, useMemo, useRef, useState } from "react";
import { ChartCard, type ChartResponse } from "./ChartCard";

type VRBuilderLivePreviewProps = {
    setReportBlocks: React.Dispatch<React.SetStateAction<ChartResponse[]>>;
    previewChart: ChartResponse | null;
    chartLoading: boolean;
};

export function VRBuilderLivePreview({
    setReportBlocks,
    previewChart,
    chartLoading,
}: VRBuilderLivePreviewProps) {
    function onAddToReport() {
        if (!previewChart) return;

        const addedToReportAtISO = new Date().toISOString();

        setReportBlocks((prev) => [
            ...prev,
            {
                ...previewChart,
                meta: {
                    ...(previewChart.meta ?? {}),
                    addedToReportAtISO,
                },
            },
        ]);
    }

    return (
        <div className="card card-border bg-base-100 w-full">
            <div className="card-body p-4 h-140 overflow-y-auto">
                <div className="pb-2 text-xs opacity-60 tracking-wide flex items-center">
                    <span>Live Preview</span>
                </div>
                <ChartCard
                    chart={previewChart}
                    height={500}
                    chartLoading={chartLoading}
                />
                <button
                    className="btn btn-primary"
                    onClick={onAddToReport}
                    disabled={!previewChart || chartLoading}
                >
                    Add to report
                </button>
            </div>
        </div>
    );
}

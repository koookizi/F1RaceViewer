import React, { useEffect, useMemo, useRef, useState } from "react";

import { ReportBlocksStrip } from "./ReportsBlocksStrip";
import { type ChartResponse } from "./ChartCard";
import type { PlotlyResult } from "./ChartCard";
import Plotly from "plotly.js-dist-min";
import JSZip from "jszip";
import { saveAs } from "file-saver";
import { jsPDF } from "jspdf";

type VRBuilderInsightsReportsProps = {
    reportBlocks: ChartResponse[];
    setReportBlocks: React.Dispatch<React.SetStateAction<ChartResponse[]>>;
};

export function VRBuilderInsightsReports({
    reportBlocks,
    setReportBlocks,
}: VRBuilderInsightsReportsProps) {
    // Helpers

    function safeFileName(name: string) {
        return name
            .trim()
            .replace(/[<>:"/\\|?*\x00-\x1F]/g, "_")
            .replace(/\s+/g, " ")
            .slice(0, 120);
    }

    function dataUrlToBlob(dataUrl: string): Blob {
        const [header, base64] = dataUrl.split(",");
        const mime = header.match(/data:(.*?);base64/)?.[1] ?? "application/octet-stream";
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        return new Blob([bytes], { type: mime });
    }

    /**
     * Render figure offscreen and return a PNG dataURL.
     * You can tweak width/height/scale for resolution.
     */
    async function figureToPngDataUrl(
        figure: PlotlyResult["figure"],
        opts?: { width?: number; height?: number; scale?: number },
    ): Promise<string> {
        const width = opts?.width ?? 1200;
        const height = opts?.height ?? 700;
        const scale = opts?.scale ?? 2;

        const div = document.createElement("div");
        div.style.position = "fixed";
        div.style.left = "-10000px";
        div.style.top = "0";
        div.style.width = `${width}px`;
        div.style.height = `${height}px`;
        document.body.appendChild(div);

        try {
            // clone layout and force size for consistent exports
            const layout = {
                ...(figure.layout ?? {}),
                width,
                height,
            };

            await Plotly.newPlot(div, figure.data, layout, {
                responsive: false,
                displayModeBar: false,
                staticPlot: true,
            });

            const dataUrl = (await Plotly.toImage(div, {
                format: "png",
                width,
                height,
                scale,
            })) as string;

            return dataUrl;
        } finally {
            try {
                Plotly.purge(div);
            } catch {}
            div.remove();
        }
    }

    function getImageSize(dataUrl: string): Promise<{ w: number; h: number }> {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight });
            img.onerror = reject;
            img.src = dataUrl;
        });
    }

    async function exportReportToPdf(reportBlocks: ChartResponse[]) {
        const pdf = new jsPDF({
            orientation: "portrait",
            unit: "pt",
            format: "a4",
        });
        const pageW = pdf.internal.pageSize.getWidth();
        const pageH = pdf.internal.pageSize.getHeight();

        const margin = 36;
        const titleSpace = 22;

        for (let i = 0; i < reportBlocks.length; i++) {
            const block = reportBlocks[i];
            const title = block.title ?? `Chart ${i + 1}`;
            if (i > 0) pdf.addPage();

            // Export chart image
            const pngDataUrl = await figureToPngDataUrl(block.result.figure, {
                width: 1400,
                height: 800,
                scale: 2,
            });

            // Title
            pdf.setFont("helvetica", "bold");
            pdf.setFontSize(14);
            pdf.text(title, margin, margin + 12);

            // Box we want to fit into
            const boxX = margin;
            const boxY = margin + titleSpace;
            const boxW = pageW - margin * 2;
            const boxH = pageH - (margin + titleSpace) - margin;

            // Compute "contain" sizing (preserve aspect ratio)
            const { w: imgW, h: imgH } = await getImageSize(pngDataUrl);
            const scale = Math.min(boxW / imgW, boxH / imgH);
            const drawW = imgW * scale;
            const drawH = imgH * scale;

            // Center within the box
            const x = boxX + (boxW - drawW) / 2;
            const y = boxY + (boxH - drawH) / 2;

            pdf.addImage(pngDataUrl, "PNG", x, y, drawW, drawH, undefined, "FAST");
        }

        pdf.save(`report_${new Date().toISOString().slice(0, 10)}.pdf`);
    }

    async function exportReportToPngZip(reportBlocks: ChartResponse[]) {
        const zip = new JSZip();
        const folder = zip.folder("png")!;

        for (let i = 0; i < reportBlocks.length; i++) {
            const block = reportBlocks[i];
            const title = safeFileName(block.title ?? `chart_${i + 1}`);

            const pngDataUrl = await figureToPngDataUrl(block.result.figure, {
                width: 1600,
                height: 900,
                scale: 2,
            });

            const blob = dataUrlToBlob(pngDataUrl);
            folder.file(`${String(i + 1).padStart(2, "0")}_${title}.png`, blob);
        }

        const zipBlob = await zip.generateAsync({ type: "blob" });
        saveAs(zipBlob, `charts_png_${new Date().toISOString().slice(0, 10)}.zip`);
    }

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
                            <span className="text-xs opacity-70">Current Report</span>
                        </div>
                    </div>

                    <div className={`px-4 pb-4`}>
                        <ReportBlocksStrip
                            reportBlocks={reportBlocks}
                            onRemove={(index) =>
                                setReportBlocks((prev) => prev.filter((_, i) => i !== index))
                            }
                        />
                    </div>
                </div>
                <div className="flex gap-3 mt-4">
                    <button
                        className="btn btn-primary"
                        onClick={() => {
                            exportReportToPngZip(reportBlocks);
                        }}
                        disabled={!reportBlocks.length}
                    >
                        Export PNGs
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={() => {
                            exportReportToPdf(reportBlocks);
                        }}
                        disabled={!reportBlocks.length}
                    >
                        Export PDF
                    </button>
                </div>
            </div>
        </div>
    );
}

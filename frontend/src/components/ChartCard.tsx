import Plot from "react-plotly.js";

export type PlotlyResult = {
    type: "plotly";
    figure: { data: any[]; layout: any; frames?: any[] };
};

export type ChartResponse = {
    title?: string;
    result: PlotlyResult;

    meta?: {
        createdAtISO?: string; 
        addedToReportAtISO?: string;
        templateId?: string;
        intent?: string;
        year?: string;
        country?: string;
        session_name?: string;

        inputs?: Record<string, any>;
    };
};

/**
 * Wrapper component for displaying chart-based visualisations.
 *
 * Provides a consistent layout and styling for Plotly charts and
 * related visual outputs within the application.
 */
export function ChartCard({
    chart,
    height = 420,
    chartLoading,
}: {
    chart: ChartResponse | null;
    height?: number;
    chartLoading: boolean;
}) {
    if (chartLoading) {
        return <div className="skeleton w-auto" style={{ height }}></div>;
    }
    if (!chart) return <div style={{ height }}>No chart yet.</div>;

    const { title, result } = chart;

    return (
        <div>
            {result.type === "plotly" && (
                <div style={{ height }}>
                    <Plot
                        data={result.figure.data}
                        layout={{ ...result.figure.layout, autosize: true }}
                        frames={result.figure.frames}
                        config={{ responsive: true, displaylogo: false }}
                        style={{ width: "100%", height: "100%" }}
                        useResizeHandler
                    />
                </div>
            )}
        </div>
    );
}

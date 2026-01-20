import Plot from "react-plotly.js";

type PlotlyResult = {
    type: "plotly";
    figure: { data: any[]; layout: any; frames?: any[] };
};

type TableResult = {
    type: "table";
    columns: string[];
    rows: (string | number | boolean | null)[][];
};

export type ChartResponse = {
    title?: string;
    result: PlotlyResult | TableResult;

    // ✅ new optional metadata (won’t break existing code)
    meta?: {
        createdAtISO?: string; // when the chart was generated (optional)
        addedToReportAtISO?: string; // when user clicked “Add to report” (this is what you want)
        templateId?: string;
        intent?: string;
        year?: string;
        country?: string;
        session_name?: string;

        // snapshot of the inputs used to generate that chart
        inputs?: Record<string, any>;
    };
};

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
            {result.type === "plotly" ? (
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
            ) : (
                <div style={{ height, overflow: "auto" }}>
                    <table
                        style={{ width: "100%", borderCollapse: "collapse" }}
                    >
                        <thead>
                            <tr>
                                {result.columns.map((c) => (
                                    <th
                                        key={c}
                                        style={{
                                            textAlign: "left",
                                            padding: 8,
                                            borderBottom: "1px solid #333",
                                        }}
                                    >
                                        {c}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {result.rows.map((row, i) => (
                                <tr key={i}>
                                    {row.map((cell, j) => (
                                        <td
                                            key={j}
                                            style={{
                                                padding: 8,
                                                borderBottom: "1px solid #222",
                                            }}
                                        >
                                            {String(cell)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

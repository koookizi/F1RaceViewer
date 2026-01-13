import React from "react";
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

type ChartApiResponse = {
    title?: string;
    result: PlotlyResult | TableResult;
};

type ChartCardProps = {
    url: string; // full URL including path params
    query?: Record<string, string | number | boolean | undefined>;
    height?: number;
};

function buildUrl(url: string, query?: ChartCardProps["query"]) {
    const qs = new URLSearchParams();
    if (query) {
        Object.entries(query).forEach(([k, v]) => {
            if (v === undefined) return;
            qs.set(k, String(v));
        });
    }
    const glue = url.includes("?") ? "&" : "?";
    return qs.toString() ? `${url}${glue}${qs.toString()}` : url;
}

export function ChartCard({ url, query, height = 420 }: ChartCardProps) {
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);
    const [data, setData] = React.useState<ChartApiResponse | null>(null);

    const finalUrl = React.useMemo(() => buildUrl(url, query), [url, JSON.stringify(query ?? {})]);

    React.useEffect(() => {
        const controller = new AbortController();

        async function run() {
            try {
                setLoading(true);
                setError(null);

                const res = await fetch(finalUrl, { signal: controller.signal });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);

                const json = (await res.json()) as ChartApiResponse;
                setData(json);
            } catch (e: any) {
                if (e.name !== "AbortError") setError(e?.message ?? "Failed to load chart");
            } finally {
                setLoading(false);
            }
        }

        run();
        return () => controller.abort();
    }, [finalUrl]);

    if (loading) return <div style={{ height }}>Loading chart…</div>;
    if (error) return <div style={{ height, color: "red" }}>Error: {error}</div>;
    if (!data) return <div style={{ height }}>No data.</div>;

    return (
        <div>
            {data.title ? <h3 style={{ margin: "0 0 8px 0" }}>{data.title}</h3> : null}

            <ChartResultRenderer result={data.result} height={height} />
        </div>
    );
}

function ChartResultRenderer({
    result,
    height,
}: {
    result: ChartApiResponse["result"];
    height: number;
}) {
    if (result.type === "plotly") {
        const fig = result.figure;
        return (
            <div style={{ height }}>
                <Plot
                    data={fig.data}
                    layout={{ ...fig.layout, autosize: true }}
                    frames={fig.frames}
                    config={{ responsive: true, displaylogo: false }}
                    style={{ width: "100%", height: "100%" }}
                    useResizeHandler
                />
            </div>
        );
    }

    // Table fallback (for your Season → "Who can still win WDC?")
    if (result.type === "table") {
        return (
            <div style={{ height, overflow: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
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
                                        style={{ padding: 8, borderBottom: "1px solid #222" }}
                                    >
                                        {String(cell)}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }

    return null;
}

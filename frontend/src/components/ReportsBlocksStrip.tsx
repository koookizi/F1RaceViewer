import type { ChartResponse } from "./ChartCard";

/**
 * Renders a collection of report blocks in a horizontal layout.
 *
 * Used to display multiple generated insights or visual outputs in a
 * structured and scrollable format.
 */
export function ReportBlocksStrip({
    reportBlocks,
    onRemove,
}: {
    reportBlocks: ChartResponse[];
    onRemove: (index: number) => void;
}) {
    return (
        <div className="overflow-x-auto">
            <div className="flex gap-3 p-2 snap-x snap-mandatory">
                {reportBlocks.map((b, i) => {
                    const added = b.meta?.addedToReportAtISO;
                    const inputs = b.meta?.inputs ?? {};

                    return (
                        <div
                            key={`${b.title ?? "block"}-${i}`}
                            className="card card-border bg-base-100 w-96 shrink-0 snap-start"
                        >
                            <div className="card-body p-4">
                                <div className="flex items-start justify-between gap-2">
                                    <div className="min-w-0">
                                        <div className="font-semibold truncate">
                                            {b.title ?? "Untitled chart"}
                                        </div>
                                        <div className="text-xs opacity-60 mt-1">
                                            Added:{" "}
                                            {added ? formatISO(added) : "—"}
                                        </div>
                                    </div>

                                    <button
                                        className="btn btn-xs"
                                        onClick={() => onRemove(i)}
                                    >
                                        Remove
                                    </button>
                                </div>

                                <div className="mt-3 text-sm">
                                    <InputsSummary inputs={inputs} />
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function formatISO(iso: string) {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function InputsSummary({ inputs }: { inputs: Record<string, any> }) {
    // turn inputs object into readable rows
    const rows = Object.entries(inputs)
        .filter(
            ([_, v]) =>
                v !== undefined &&
                v !== null &&
                v !== "" &&
                !(Array.isArray(v) && v.length === 0)
        )
        .map(([k, v]) => [prettyKey(k), prettyVal(v)] as const);

    if (!rows.length) return <div className="opacity-60">No inputs saved.</div>;

    return (
        <div className="grid gap-2">
            {rows.map(([k, v]) => (
                <div key={k} className="grid grid-cols-[120px_1fr] gap-2">
                    <div className="text-xs opacity-60">{k}</div>
                    <div className="text-xs truncate" title={v}>
                        {v}
                    </div>
                </div>
            ))}
        </div>
    );
}

function prettyKey(k: string) {
    return k
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/_/g, " ")
        .replace(/^./, (c) => c.toUpperCase());
}

function prettyVal(v: any) {
    if (Array.isArray(v)) return v.join(", ");
    if (typeof v === "boolean") return v ? "Yes" : "No";
    return String(v);
}

import { useEffect, useRef } from "react";

type Result = {
  driverNumber: string;
  name: string;
  team_color?: string | null;
  gridPos: number | string | null;
};

interface StartingGridProps {
  results: Result[];
}

export function StartingGrid({ results }: StartingGridProps) {
  // 1. Normalise gridPos (string/float/null → number|null)
  const clean = results
    .map((r) => {
      const num = r.gridPos == null ? NaN : Number(r.gridPos);
      const gridPosInt =
        Number.isFinite(num) && num > 0 ? Math.round(num) : null;
      return { ...r, gridPosInt };
    })
    .filter((r) => r.gridPosInt !== null)
    .sort((a, b) => a.gridPosInt! - b.gridPosInt!);

  // 2. Split into TWO LANES
  const topLane = clean.filter((d) => d.gridPosInt! % 2 === 1); // P1, P3, P5…
  const bottomLane = clean.filter((d) => d.gridPosInt! % 2 === 0); // P2, P4, P6…

  // 3. Card component for each driver
  function Card({ driver }: { driver: (typeof clean)[number] }) {
    return (
      <div className="flex">
        <div
          className="
                flex items-center gap-3 rounded-2xl px-4 py-3
                bg-base-200 shadow-sm border-l-4 w-64
                "
          style={{ borderLeftColor: driver.team_color || "#888" }}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-base-300 text-xs font-semibold">
            {driver.driverNumber}
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold leading-tight">
              {driver.name}
            </span>
            <span className="text-[11px] opacity-70">P{driver.gridPosInt}</span>
          </div>
        </div>
        <div className="h-auto ms-3 w-3 border-r-2 border-t-2 border-b-2 border-gray-500 rounded-r-sm" />
      </div>
    );
  }

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = scrollRef.current.scrollWidth;
    }
  }, [results]);

  // 4. Render lanes + finish line
  return (
    <div ref={scrollRef} className="w-full overflow-x-auto">
      <div className="inline-flex items-stretch gap-4 min-w-[720px] px-4 py-4">
        {/* ========================= GRID AREA ========================= */}
        <div className="flex-1 pr-4 relative border-r border-dashed border-gray-500">
          <div className="flex flex-col gap-4">
            <div
              className="w-full h-3 bg-[length:120px_120px]"
              style={{
                backgroundImage:
                  "linear-gradient(90deg, #ff000070 25%, #ffffff70 25%, #ffffff70 50%, #ff000070 50%, #ff000070 75%, #ffffff70 75%, #ffffff70 100%)",
              }}
            ></div>

            {/* Top Lane (Odd positions) — reversed so P1 is closest to finish line */}
            <div className="flex flex-row-reverse gap-4 me-15">
              {topLane.map((d) => (
                <Card key={`top-${d.driverNumber}`} driver={d} />
              ))}
            </div>

            {/* Bottom Lane (Even positions) */}
            <div className="flex flex-row-reverse gap-4 me-22">
              {bottomLane.map((d) => (
                <Card key={`bottom-${d.driverNumber}`} driver={d} />
              ))}
            </div>

            <div
              className="w-full h-3 bg-[length:120px_120px]"
              style={{
                backgroundImage:
                  "linear-gradient(90deg, #ff000070 25%, #ffffff70 25%, #ffffff70 50%, #ff000070 50%, #ff000070 75%, #ffffff70 75%, #ffffff70 100%)",
              }}
            ></div>
          </div>

          {/* Vertical GRID label */}
          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center justify-center translate-x-1 text-[10px] uppercase tracking-[0.2em] text-neutral-500 rotate-90">
            Starting Grid
          </span>
        </div>

        {/* ========================= FINISH LINE ========================= */}
        <div className="w-16 relative flex items-center justify-center">
          <div
            className="
              h-full w-3
              bg-[length:8px_8px]
              bg-[linear-gradient(45deg,#000_25%,transparent_25%,transparent_50%,#000_50%,#000_75%,transparent_75%,transparent)]
              border-l border-neutral-700
            "
          />
          <span className="pointer-events-none absolute inset-y-0 right-3.5 flex items-center justify-center translate-x-1 text-[10px] uppercase tracking-[0.2em] text-neutral-500 rotate-90">
            Finish
          </span>
        </div>
      </div>
    </div>
  );
}

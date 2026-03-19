import { TelemetryRing } from "./TelemetryRing";

type Item = {
  percent: number;
  valueText: string;
  label: string;
  color: string;
  subLabel?: string;
};

/**
 * Displays a single telemetry value in a compact format.
 *
 * Designed for quick, readable presentation of key metrics such as
 * speed, throttle or braking during playback.
 */
export function TelemetryPill({ items }: { items: Item[] }) {
  return (
    <div className="inline-flex items-end gap-4 rounded-full">
      {items.map((it) => (
        <div key={it.label} className="flex flex-col items-center">
          <TelemetryRing
            percent={it.percent}
            valueText={it.valueText}
            label={it.label}
            color={it.color}
            size={56}
            strokeWidth={10}
            gapRatio={0.82}
          />

          {/* semi-transparent text below */}
          {it.subLabel && (
            <span className="text-[10px] text-white/50 tracking-wide">
              {it.subLabel}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

import React from "react";

export type TagOption = {
  id: string | number;
  label: string;
  disabled?: boolean;
};

type TagGroupProps = {
  label?: string;
  options: TagOption[];
  value: Array<TagOption["id"]>;
  onChange: (nextIds: Array<TagOption["id"]>) => void;
  className?: string;
};

export function TagGroup({
  label,
  options,
  value,
  onChange,
  className = "",
}: TagGroupProps) {
  function toggle(id: TagOption["id"]) {
    if (value.includes(id)) {
      onChange(value.filter((v) => v !== id));
    } else {
      onChange([...value, id]);
    }
  }

  return (
    <div className={className}>
      {label && (
        <div className="mb-1 text-xs font-medium opacity-70">{label}</div>
      )}

      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const selected = value.includes(opt.id);

          return (
            <button
              key={opt.id}
              type="button"
              disabled={opt.disabled}
              onClick={() => toggle(opt.id)}
              className={[
                "badge cursor-pointer select-none",
                selected ? "badge-primary" : "badge-outline",
                opt.disabled ? "opacity-40 cursor-not-allowed" : "",
              ].join(" ")}
              aria-pressed={selected}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

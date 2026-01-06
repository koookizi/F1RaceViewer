import React, { useEffect, useMemo, useRef, useState } from "react";

export type MultiSelectOption = {
  id: string | number;
  label: string;
  disabled?: boolean;
};

type MultiSelectProps = {
  label?: string;
  options: MultiSelectOption[];
  value: Array<MultiSelectOption["id"]>;
  onChange: (nextIds: Array<MultiSelectOption["id"]>) => void;
  placeholder?: string;
  className?: string;

  /** Controls width without forcing a huge control */
  widthClassName?: string; // e.g. "w-full", "w-72", "w-80"
  /** Caps chip overflow height so it stays compact */
  maxChipsRows?: number; // default 2
};

export function MultiSelect({
  label,
  options,
  value,
  onChange,
  placeholder = "Select…",
  className = "",
  widthClassName = "w-72",
  maxChipsRows = 2,
}: MultiSelectProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  // Close on click outside / Escape
  useEffect(() => {
    function onDocMouseDown(e: MouseEvent) {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    function onDocKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocMouseDown);
    document.addEventListener("keydown", onDocKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      document.removeEventListener("keydown", onDocKeyDown);
    };
  }, []);

  const selectedSet = useMemo(() => new Set(value), [value]);

  const selectedOptions = useMemo(() => {
    return options.filter((o) => selectedSet.has(o.id));
  }, [options, selectedSet]);

  const filteredOptions = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = q
      ? options.filter((o) => o.label.toLowerCase().includes(q))
      : options;

    // Keep stable active index
    return list;
  }, [options, query]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, open]);

  function toggle(id: MultiSelectOption["id"]) {
    if (selectedSet.has(id)) onChange(value.filter((x) => x !== id));
    else onChange([...value, id]);
  }

  function remove(id: MultiSelectOption["id"]) {
    onChange(value.filter((x) => x !== id));
  }

  const maxChipsHeight = maxChipsRows * 28; // approx per row height

  function focusAndOpen() {
    setOpen(true);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function onInputKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open && (e.key === "ArrowDown" || e.key === "Enter")) {
      e.preventDefault();
      focusAndOpen();
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filteredOptions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = filteredOptions[activeIndex];
      if (item && !item.disabled) toggle(item.id);
    } else if (e.key === "Backspace") {
      // If query empty, remove last selected
      if (query === "" && selectedOptions.length > 0) {
        remove(selectedOptions[selectedOptions.length - 1].id);
      }
    }
  }

  return (
    <div ref={rootRef} className={`${widthClassName} ${className}`}>
      {label ? (
        <div className="label py-1">
          <span className="label-text text-sm">{label}</span>
        </div>
      ) : null}

      {/* Compact control */}
      <div
        className={[
          "rounded-lg bg-base-200 border border-base-300",
          "px-2 py-1.5",
          "flex items-center gap-2",
          "cursor-text",
          open ? "ring-2 ring-primary ring-offset-2 ring-offset-base-100" : "",
        ].join(" ")}
        onClick={focusAndOpen}
      >
        {/* Chips area (compact, capped height) */}
        <div
          className="flex flex-wrap gap-1 flex-1 min-w-0 overflow-auto pr-1"
          style={{ maxHeight: maxChipsHeight }}
        >
          {selectedOptions.length === 0 ? (
            <span className="text-sm opacity-60 select-none px-1">
              {placeholder}
            </span>
          ) : (
            selectedOptions.map((opt) => (
              <span key={opt.id} className="badge badge-primary badge-sm gap-1">
                <span className="truncate max-w-[10rem]">{opt.label}</span>
                <button
                  type="button"
                  className="btn btn-ghost btn-xs px-1 h-4 min-h-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    remove(opt.id);
                  }}
                  aria-label={`Remove ${opt.label}`}
                  title={`Remove ${opt.label}`}
                >
                  ✕
                </button>
              </span>
            ))
          )}

          {/* Search input sits inline with chips */}
          <input
            ref={inputRef}
            className="bg-transparent outline-none text-sm px-1 flex-1 min-w-[6ch]"
            placeholder={selectedOptions.length ? "" : undefined}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onInputKeyDown}
            onFocus={() => setOpen(true)}
          />
        </div>

        {/* Right-side actions */}
        <div className="flex items-center gap-1">
          {value.length > 0 && (
            <button
              type="button"
              className="btn btn-ghost btn-xs"
              onClick={(e) => {
                e.stopPropagation();
                onChange([]);
                setQuery("");
                inputRef.current?.focus();
              }}
              aria-label="Clear selection"
              title="Clear"
            >
              Clear
            </button>
          )}

          <button
            type="button"
            className="btn btn-primary btn-xs btn-circle"
            onClick={(e) => {
              e.stopPropagation();
              setOpen((v) => !v);
              if (!open) inputRef.current?.focus();
            }}
            aria-label="Toggle menu"
            title="Toggle"
          >
            ▾
          </button>
        </div>
      </div>

      {/* Dropdown */}
      {open && (
        <div className="mt-2 rounded-lg bg-base-100 shadow border border-base-300 p-1">
          <div className="max-h-56 overflow-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-2 py-2 text-sm opacity-60">No results</div>
            ) : (
              <ul className="menu menu-sm">
                {filteredOptions.map((opt, idx) => {
                  const checked = selectedSet.has(opt.id);
                  const active = idx === activeIndex;

                  return (
                    <li key={opt.id}>
                      <button
                        type="button"
                        disabled={opt.disabled}
                        className={[
                          "flex items-center justify-between",
                          active ? "bg-base-200" : "",
                          opt.disabled ? "opacity-40 cursor-not-allowed" : "",
                        ].join(" ")}
                        onMouseEnter={() => setActiveIndex(idx)}
                        onClick={() => {
                          if (opt.disabled) return;
                          toggle(opt.id);
                        }}
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            className="checkbox checkbox-xs"
                            readOnly
                            checked={checked}
                          />
                          <span className="text-sm">{opt.label}</span>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="mt-1 px-1 pb-1 flex items-center justify-between">
            <span className="text-xs opacity-60">{value.length} selected</span>
            <button
              type="button"
              className="btn btn-primary btn-xs"
              onClick={() => setOpen(false)}
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

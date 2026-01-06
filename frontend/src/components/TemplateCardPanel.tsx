import React from "react";

export type Template = {
  id: string;
  intent: string;
  title: string;
  description?: string;
  tags?: string[];
};

type TemplateCardPanelProps = {
  intent: string;
  templates: Template[];
  heightClassName?: string;
  onSelectTemplate?: (t: Template) => void;
  selectedTemplateId?: string | null;
};

export function TemplateCardPanel({
  intent,
  templates,
  heightClassName = "h-80",
  onSelectTemplate,
  selectedTemplateId = null,
}: TemplateCardPanelProps) {
  const filtered = React.useMemo(
    () => templates.filter((t) => t.intent === intent),
    [templates, intent]
  );

  return (
    <div
      className={[
        "rounded-xl border",
        "bg-base-200 border-base-300/50",
        "shadow-sm",
      ].join(" ")}
    >
      <div className="px-4 pt-4 pb-2 flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-xs opacity-70">Templates</span>
          <span className="text-sm font-semibold">
            {intent || "Select an intent"}
          </span>
        </div>

        <span className="badge badge-ghost badge-sm">
          {filtered.length} found
        </span>
      </div>

      <div className={`px-4 pb-4 ${heightClassName}`}>
        <div
          className={[
            "h-full overflow-y-auto pr-1",
            "grid grid-cols-1 gap-3",
          ].join(" ")}
        >
          {intent && filtered.length === 0 && (
            <div className="rounded-lg bg-base-100/30 border border-base-300/40 p-4 text-sm opacity-70">
              No templates available for this intent yet.
            </div>
          )}

          {!intent && (
            <div className="rounded-lg bg-base-100/30 border border-base-300/40 p-4 text-sm opacity-70">
              Select an intent to view templates.
            </div>
          )}

          {filtered.map((t) => {
            const selected = selectedTemplateId === t.id;

            return (
              <button
                key={t.id}
                type="button"
                onClick={() => onSelectTemplate?.(t)}
                className={[
                  "text-left w-full",
                  "rounded-xl border p-4",
                  "bg-base-100/40 border-base-300/40",
                  "hover:bg-base-100/60 hover:border-base-300/60",
                  "transition",
                  selected ? "ring-2 ring-primary ring-inset" : "",
                ].join(" ")}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-semibold truncate">
                      {t.title}
                    </div>
                    {t.description && (
                      <div className="mt-1 text-xs opacity-70 line-clamp-2">
                        {t.description}
                      </div>
                    )}
                  </div>

                  <span className="badge badge-primary badge-sm shrink-0">
                    Use
                  </span>
                </div>

                {t.tags && t.tags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {t.tags.slice(0, 6).map((tag) => (
                      <span key={tag} className="badge badge-ghost badge-sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

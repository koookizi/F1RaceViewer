import * as React from "react";

type FlagProps = React.SVGProps<SVGSVGElement> & {
  /** Primary fabric color (defaults to currentColor for mono flags) */
  fabric?: string;
  /** Secondary accent (used by patterns like stripes/checkers) */
  accent?: string;
  /** Pole color */
  pole?: string;
  /** Outline stroke color */
  stroke?: string;
};

const common = {
  viewBox: "0 0 24 24",
  fill: "none",
} as const;

/**
 * Base flag geometry:
 * - Pole at x=5
 * - Fabric with gentle wave, rounded corners
 * - Outer stroke for crisp UI at small sizes
 */
function FlagBase({
  children,
  pole = "currentColor",
  stroke = "currentColor",
  ...props
}: FlagProps & { children: React.ReactNode }) {
  return (
    <svg {...common} {...props} aria-hidden="true">
      {/* Pole */}
      <path d="M5 3v18" stroke={pole} strokeWidth="1.6" strokeLinecap="round" />
      {/* Fabric outline */}
      <path
        d="M7.2 5.4c2.1-1.2 4.2-1.2 6.3 0 2.1 1.2 4.2 1.2 6.3 0v8.2c-2.1 1.2-4.2 1.2-6.3 0-2.1-1.2-4.2-1.2-6.3 0V5.4Z"
        stroke={stroke}
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      {/* Clip for fills/patterns */}
      <defs>
        <clipPath id="flag-clip">
          <path d="M7.2 5.4c2.1-1.2 4.2-1.2 6.3 0 2.1 1.2 4.2 1.2 6.3 0v8.2c-2.1 1.2-4.2 1.2-6.3 0-2.1-1.2-4.2-1.2-6.3 0V5.4Z" />
        </clipPath>
      </defs>

      <g clipPath="url(#flag-clip)">{children}</g>

      {/* Small pole cap */}
      <circle cx="5" cy="3" r="1.1" fill={pole} />
    </svg>
  );
}

export function FlagSolid({
  fabric = "currentColor",
  stroke = "currentColor",
  pole = "currentColor",
  ...props
}: FlagProps) {
  return (
    <FlagBase stroke={stroke} pole={pole} {...props}>
      <rect x="6.4" y="4.6" width="14.2" height="10.8" fill={fabric} />
      {/* Subtle wave highlight */}
      <path
        d="M7.2 8.2c2.1-1.2 4.2-1.2 6.3 0 2.1 1.2 4.2 1.2 6.3 0"
        stroke="rgba(255,255,255,0.35)"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </FlagBase>
  );
}

/** Specific single-color flags */
export const FlagYellow = (p: FlagProps) => (
  <FlagSolid fabric={p.fabric ?? "#F7D11E"} {...p} />
);
export const FlagRed = (p: FlagProps) => (
  <FlagSolid fabric={p.fabric ?? "#E11D2E"} {...p} />
);
export const FlagGreen = (p: FlagProps) => (
  <FlagSolid fabric={p.fabric ?? "#16A34A"} {...p} />
);
export const FlagBlue = (p: FlagProps) => (
  <FlagSolid fabric={p.fabric ?? "#2563EB"} {...p} />
);
export const FlagWhite = (p: FlagProps) => (
  <FlagSolid
    fabric={p.fabric ?? "#FFFFFF"}
    stroke={p.stroke ?? "#111827"}
    pole={p.pole ?? "#111827"}
    {...p}
  />
);
export const FlagBlack = (p: FlagProps) => (
  <FlagSolid
    fabric={p.fabric ?? "#111827"}
    stroke={p.stroke ?? "#111827"}
    pole={p.pole ?? "#111827"}
    {...p}
  />
);

/** Black/White diagonal warning flag (track limits / unsporting etc.) */
export function FlagBlackWhite({
  fabric,
  accent,
  stroke = "#111827",
  pole = "#111827",
  ...props
}: FlagProps) {
  const white = fabric ?? "#FFFFFF";
  const black = accent ?? "#111827";
  return (
    <FlagBase stroke={stroke} pole={pole} {...props}>
      <rect x="6.4" y="4.6" width="14.2" height="10.8" fill={white} />
      <path d="M6.4 15.4L20.6 4.6H23v3.2L8.2 15.4H6.4Z" fill={black} />
      <path
        d="M7.2 8.2c2.1-1.2 4.2-1.2 6.3 0 2.1 1.2 4.2 1.2 6.3 0"
        stroke="rgba(0,0,0,0.18)"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </FlagBase>
  );
}

/** Yellow/Red striped flag (slippery surface) */
export function FlagYellowRedStripes({
  fabric,
  accent,
  stroke = "currentColor",
  pole = "currentColor",
  ...props
}: FlagProps) {
  const yellow = fabric ?? "#F7D11E";
  const red = accent ?? "#E11D2E";
  return (
    <FlagBase stroke={stroke} pole={pole} {...props}>
      <rect x="6.4" y="4.6" width="14.2" height="10.8" fill={yellow} />
      {/* diagonal stripes */}
      <g opacity="0.95">
        <path d="M6.4 13.6L15.2 4.6h2.1L8.5 15.4H6.4v-1.8Z" fill={red} />
        <path d="M10.2 15.4L19 4.6h2.1l-8.8 10.8h-2.1Z" fill={red} />
        <path d="M14 15.4L22.8 4.6H23v1.6L16.1 15.4H14Z" fill={red} />
      </g>
      <path
        d="M7.2 8.2c2.1-1.2 4.2-1.2 6.3 0 2.1 1.2 4.2 1.2 6.3 0"
        stroke="rgba(255,255,255,0.28)"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </FlagBase>
  );
}

/** Chequered flag */
export function FlagChequered({
  fabric,
  accent,
  stroke = "#111827",
  pole = "#111827",
  ...props
}: FlagProps) {
  const white = fabric ?? "#FFFFFF";
  const black = accent ?? "#111827";

  return (
    <FlagBase stroke={stroke} pole={pole} {...props}>
      <rect x="6.4" y="4.6" width="14.2" height="10.8" fill={white} />
      {/* checker grid 4x3 */}
      {Array.from({ length: 12 }).map((_, i) => {
        const col = i % 4;
        const row = Math.floor(i / 4);
        const isBlack = (row + col) % 2 === 0;
        const x = 6.6 + col * 3.45;
        const y = 4.8 + row * 3.55;
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width="3.35"
            height="3.45"
            fill={isBlack ? black : white}
            opacity="0.98"
          />
        );
      })}
      <path
        d="M7.2 8.2c2.1-1.2 4.2-1.2 6.3 0 2.1 1.2 4.2 1.2 6.3 0"
        stroke="rgba(0,0,0,0.14)"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </FlagBase>
  );
}

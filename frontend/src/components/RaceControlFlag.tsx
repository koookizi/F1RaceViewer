import {
  FlagGreen,
  FlagYellow,
  FlagRed,
  FlagBlue,
  FlagBlack,
  FlagWhite,
  FlagBlackWhite,
  FlagYellowRedStripes,
  FlagChequered,
} from "./Flags";

type RaceControlFlagProps = {
  flag: string | null;
  className?: string;
};

function normalizeFlag(flag: string | null): string | null {
  if (!flag) return null;
  return flag.trim().toUpperCase();
}

export function RaceControlFlag({ flag, className }: RaceControlFlagProps) {
  const f = normalizeFlag(flag);

  // default size for list column
  const p = { className: className ?? "w-10 h-10" };

  if (!f) return null;

  switch (f) {
    case "GREEN":
    case "CLEAR":
      return <FlagGreen {...p} />;

    case "YELLOW":
      return <FlagYellow {...p} />;

    case "DOUBLE YELLOW":
    case "DOUBLE_YELLOW":
      return <FlagYellow {...p} />;

    case "RED":
      return <FlagRed {...p} />;

    case "BLUE":
      return <FlagBlue {...p} />;

    case "BLACK":
      return <FlagBlack {...p} />;

    case "WHITE":
      return <FlagWhite {...p} />;

    case "BLACK AND WHITE":
    case "BLACK_AND_WHITE":
    case "BLACK WHITE":
    case "BLACK_WHITE":
      return <FlagBlackWhite {...p} />;

    case "YELLOW AND RED":
    case "YELLOW_RED":
    case "YELLOW RED":
    case "STRIPED":
      return <FlagYellowRedStripes {...p} />;

    case "CHEQUERED":
    case "CHECKERED":
      return <FlagChequered {...p} />;

    default:
      return null;
  }
}

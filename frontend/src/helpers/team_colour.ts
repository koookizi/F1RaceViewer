import type { LeaderboardApiResponse } from "../types";

export function teamBgByDriver(
  data: LeaderboardApiResponse | null,
  driver: number | string | null,
  alpha: string | "opaque" = "33"
): string | undefined {
  if (!data) return undefined;

  const d = data.drivers.find((drv) =>
    typeof driver === "number"
      ? drv.driver_number === driver
      : drv.driver_code === driver
  );

  if (!d?.team_colour) return undefined;

  const hex = d.team_colour.startsWith("#")
    ? d.team_colour.slice(1)
    : d.team_colour;

  if (alpha === "opaque") {
    return `#${hex}`;
  }

  return `#${hex}${alpha}`;
}

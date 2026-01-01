import type { LeaderboardApiResponse } from "../types";

export function teamBgByDriverNumber(
  data: LeaderboardApiResponse | null,
  driverNumber: number,
  alphaHex = "33"
) {
  const raw = data?.drivers.find(
    (d) => d.driver_number === driverNumber
  )?.team_colour;
  if (!raw) return undefined;

  const hex = raw.startsWith("#") ? raw.slice(1) : raw;
  return `#${hex}${alphaHex}`;
}

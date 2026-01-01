import type { LeaderboardApiResponse } from "../types";

export function getDriverAbbreviation(
  leaderboard: LeaderboardApiResponse | null,
  driverNumber: number | null
): string | null {
  if (!leaderboard || driverNumber == null) return null;

  const driver = leaderboard.drivers.find(
    (d) => d.driver_number === driverNumber
  );

  return driver?.driver_code ?? null;
}

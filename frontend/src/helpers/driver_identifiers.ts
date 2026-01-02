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

export function getDriverFullNameByNumber(
  leaderboardData: LeaderboardApiResponse | null,
  driverNumber: number | null
): string | null {
  if (!leaderboardData) return null;

  const driver = leaderboardData.drivers.find(
    (d) => d.driver_number === driverNumber
  );

  if (!driver) return null;

  // adjust field names if yours differ
  return `${driver.driver_fullName}`;
}

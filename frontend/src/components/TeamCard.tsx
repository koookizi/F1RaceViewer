import type { driverData } from "../types.ts";

type DriverCardProps = {
    driver: driverData;
    team: string;
};

export default function DriverCard({ driver, team }: DriverCardProps) {
    const teamColor = driver.team_colour || "000000";

    return (
        <div
            className="
        card w-auto h-24
        border border-black/10
        shadow-lg overflow-hidden
        transition
        hover:shadow-xl hover:scale-[1.02]
      "
            style={{
                background: `
    linear-gradient(
      135deg,
      #${teamColor}cc 0%,
      #${teamColor}80 40%,
      #000000cc 100%
    )
  `,
            }}
        >
            <div className="card-body p-3 flex flex-row items-center gap-4">
                {/* Team details */}
                <div className="flex flex-col justify-center leading-tight">
                    <div className="text-white font-semibold text-lg">{team}</div>
                    <div className="text-white/80 text-sm">
                        #{driver.driver_number} · {driver.name_acronym}
                    </div>
                </div>
            </div>
        </div>
    );
}

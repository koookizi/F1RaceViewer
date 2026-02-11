import type { TeamDriverData } from "../types.ts";

type DriverCardProps = {
    driver: TeamDriverData;
};

export default function DriverCard({ driver }: DriverCardProps) {
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
                {/* Driver headshot */}
                <img
                    src={driver.headshot_url}
                    alt={driver.full_name}
                    className="
            w-14 h-14
            rounded-full object-cover
            border border-white/40
            bg-white/10
          "
                />

                {/* Driver details */}
                <div className="flex flex-col justify-center leading-tight">
                    <div className="text-white font-semibold text-lg">
                        {driver.first_name} {driver.last_name}
                    </div>
                    <div className="text-white/80 text-sm">
                        #{driver.driver_number} · {driver.name_acronym}
                    </div>
                </div>
            </div>
        </div>
    );
}

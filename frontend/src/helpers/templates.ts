export type Intent = "Pace" | "Strategy" | "Telemetry" | "Positions" | "Season";

export type Template = {
    id: string;
    intent: Intent;
    title: string;
    description: string;
    tags: string[];
};

export const TEMPLATES: Template[] = [
    // --- Pace ---
    {
        id: "t1",
        intent: "Pace",
        title: "Driver laptimes scatterplot (consistency/outliers)",
        description:
            "Plots every lap time for selected drivers to quickly spot consistency, traffic-affected laps, and outliers.",
        tags: ["Pace", "Consistency", "Outliers", "Traffic", "Lap-by-lap"],
    },
    {
        id: "t2",
        intent: "Pace",
        title: "Driver laptimes distribution (box/violin/hist)",
        description:
            "Shows the overall spread of lap times per driver, making it easy to compare consistency and typical pace at a glance.",
        tags: ["Pace", "Distribution", "Consistency", "Compare drivers"],
    },
    {
        id: "t3",
        intent: "Pace",
        title: "Lap time trend (line; rolling avg optional)",
        description:
            "Visualises how lap time changes across the session, useful for spotting long-run pace, tyre drop-off, and performance phases.",
        tags: ["Trend", "Degradation", "Long run", "Stints", "Compare drivers"],
    },
    {
        id: "t4",
        intent: "Pace",
        title: "Sector time breakdown (S1/S2/S3 per driver)",
        description:
            "Breaks down performance by sector so users can identify where time is gained or lost on the circuit.",
        tags: ["Sectors", "Strengths/Weaknesses", "Track analysis", "Compare"],
    },
    {
        id: "t5",
        intent: "Pace",
        title: "Speed trap comparison (I1/I2/FL/ST)",
        description:
            "Compares speed trap values to highlight top speed differences and where cars are fast along the straights.",
        tags: ["Top speed", "Power", "Straights", "Comparison"],
    },
    {
        id: "t6",
        intent: "Pace",
        title: "Team pace comparison (aggregate by team)",
        description:
            "Aggregates lap times by team to compare overall team performance rather than individual drivers.",
        tags: ["Team", "Comparison", "Summary", "Pace"],
    },

    // --- Strategy ---
    {
        id: "t7",
        intent: "Strategy",
        title: "Tyre strategy timeline (stints by compound)",
        description:
            "Shows tyre compounds and stints across the race/session to visualise strategies, pit timing, and stint lengths.",
        tags: ["Tyres", "Stints", "Pit strategy", "Timeline", "Race story"],
    },
    {
        id: "t8",
        intent: "Strategy",
        title: "Stint length comparison",
        description:
            "Compares how long each stint lasted per driver, revealing one-stops vs two-stops and alternative plans.",
        tags: ["Stints", "Pit windows", "Strategy", "Comparison"],
    },
    {
        id: "t9",
        intent: "Strategy",
        title: "Stint average pace (per stint mean/median lap time)",
        description:
            "Summarises pace per stint to compare who was quickest on each tyre run, not just on single laps.",
        tags: ["Stint pace", "Long run", "Degradation", "Strategy"],
    },
    {
        id: "t10",
        intent: "Strategy",
        title: "Pit in/out timeline (pit events across laps)",
        description:
            "Marks pit in/out events by lap to show when drivers pitted and how pit sequences shaped track position.",
        tags: ["Pit stops", "Timeline", "Race events", "Undercut/Overcut"],
    },
    {
        id: "t11",
        intent: "Strategy",
        title: "Compound performance comparison (pace by compound)",
        description:
            "Compares lap times by tyre compound to see which tyres delivered best pace and how drivers used them.",
        tags: ["Tyres", "Compound", "Pace", "Comparison"],
    },

    // --- Telemetry ---
    {
        id: "t12",
        intent: "Telemetry",
        title: "Overlay speed traces of two laps",
        description:
            "Overlays speed traces to compare two laps (two drivers or two attempts) and pinpoint where time was gained.",
        tags: ["Speed trace", "Lap compare", "Delta clues", "Driving style"],
    },
    {
        id: "t13",
        intent: "Telemetry",
        title: "Multi-channel lap overlay (speed/throttle/brake)",
        description:
            "Compares driving inputs across a lap by overlaying speed, throttle, and brake to reveal technique differences.",
        tags: ["Throttle", "Brake", "Driving inputs", "Lap compare"],
    },
    {
        id: "t14",
        intent: "Telemetry",
        title: "Gear shifts on track",
        description:
            "Maps gear usage around the circuit to show shift points, corner gears, and acceleration zones.",
        tags: ["Gears", "Track map", "Driving technique", "Power delivery"],
    },
    {
        id: "t15",
        intent: "Telemetry",
        title: "Speed visualisation on track map",
        description:
            "Colours the racing line by speed to highlight fast sections, braking zones, and minimum-speed corners.",
        tags: ["Track map", "Speed", "Corners", "Braking zones"],
    },
    {
        id: "t16",
        intent: "Telemetry",
        title: "Track map (driving line)",
        description:
            "Draws the car's path around the circuit, providing a base layer for other telemetry-based overlays.",
        tags: ["Track map", "Racing line", "Reference"],
    },
    {
        id: "t17",
        intent: "Telemetry",
        title: "Driver-ahead proximity (battle/DRS analysis)",
        description:
            "Shows how close a driver was to the car ahead, useful for analysing battles, DRS trains, and overtakes.",
        tags: ["Battles", "DRS", "Proximity", "Racecraft"],
    },

    // --- Positions ---
    {
        id: "t18",
        intent: "Positions",
        title: "Position changes during a race (multi-driver)",
        description:
            "Tracks position by lap for multiple drivers to reveal overtakes, pit cycle effects, and big swings.",
        tags: ["Positions", "Overtakes", "Race progression", "Story"],
    },
    {
        id: "t19",
        intent: "Positions",
        title: "Driver position timeline (single driver)",
        description:
            "Follows one driver's position across the session to explain their race narrative and key turning points.",
        tags: ["Driver focus", "Race story", "Positions"],
    },
    {
        id: "t20",
        intent: "Positions",
        title: "Top-10 position chart (filtered view)",
        description:
            "Shows position changes only for a selected group (e.g., top 10) to keep the chart readable and focused.",
        tags: ["Top 10", "Clarity", "Filtered", "Positions"],
    },

    // --- Season ---
    {
        id: "t21",
        intent: "Season",
        title: "Driver standings heatmap (round-by-round)",
        description:
            "Visualises standings across rounds to show momentum, consistency, and turning points in the championship.",
        tags: ["Standings", "Heatmap", "Consistency", "Championship"],
    },
    {
        id: "t22",
        intent: "Season",
        title: "Season summary (trend over rounds)",
        description:
            "Shows how points/wins accumulate over a season for drivers or teams, highlighting dominance and close fights.",
        tags: ["Season", "Trend", "Points", "Teams", "Drivers"],
    },
    {
        id: "t23",
        intent: "Season",
        title: "Who can still win the WDC?",
        description:
            "Explores championship scenarios by comparing current points with remaining opportunities across the calendar.",
        tags: ["Championship", "Scenarios", "Maths", "Remaining rounds"],
    },
];

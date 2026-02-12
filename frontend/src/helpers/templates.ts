export type Intent =
    | "Pace"
    | "Strategy"
    | "Telemetry"
    | "Positions"
    | "Season"
    | "Team Season Performance"
    | "Team Context & Affinity"
    | "Team Performance Characteristics"
    | "Driver Season Performance"
    | "Driver vs Teammate"
    | "Driver Characteristics";

export type Page = "Race" | "Team" | "Driver";

export type Template = {
    id: string;
    page: Page;
    intent: Intent;
    title: string;
    description: string;
    tags: string[];
};

export const TEMPLATES: Template[] = [
    // --# Driver Page #--
    {
        id: "t32",
        intent: "Driver Season Performance",
        page: "Driver",
        title: "Driver points per race (season trend)",
        description:
            "Shows points scored by the selected driver at each round of a season to highlight momentum shifts, standout weekends, and overall consistency.",
        tags: ["Driver", "Season", "Points", "Trend", "Consistency"],
    },
    {
        id: "t33",
        intent: "Driver Season Performance",
        page: "Driver",
        title: "Finish position distribution (consistency boxplot)",
        description:
            "Displays the distribution of finishing positions across a season to evaluate the driver's consistency and result variability.",
        tags: ["Driver", "Finishing Positions", "Consistency", "Distribution", "Season"],
    },
    {
        id: "t34",
        intent: "Driver Season Performance",
        page: "Driver",
        title: "Positions gained histogram (race execution)",
        description:
            "Shows how many places the driver typically gains or loses during races by plotting the distribution of grid-to-finish position changes.",
        tags: ["Driver", "Race Craft", "Overtaking", "Positions Gained", "Execution"],
    },
    {
        id: "t35",
        intent: "Driver vs Teammate",
        page: "Driver",
        title: "Points vs teammate (season comparison)",
        description:
            "Compares total season points between the selected driver and their teammate to summarise championship contribution within the same car.",
        tags: ["Driver", "Teammate", "Points", "Comparison", "Season"],
    },
    {
        id: "t36",
        intent: "Driver vs Teammate",
        page: "Driver",
        title: "Qualifying head-to-head vs teammate",
        description:
            "Counts how often the driver out-qualifies their teammate across the season to measure one-lap performance within equal machinery.",
        tags: ["Driver", "Qualifying", "Teammate", "Head-to-Head", "One-Lap Pace"],
    },
    {
        id: "t37",
        intent: "Driver vs Teammate",
        page: "Driver",
        title: "Race pace delta vs teammate (boxplot)",
        description:
            "Shows the distribution of lap-time deltas between the driver and their teammate across the season to isolate relative race pace beyond strategy and luck.",
        tags: ["Driver", "Pace", "Teammate", "Delta", "Lap Time"],
    },
    {
        id: "t38",
        intent: "Driver Characteristics",
        page: "Driver",
        title: "Tyre degradation profile (season aggregate)",
        description:
            "Plots lap-time evolution within stints (by compound) aggregated across the season to evaluate the driver's tyre management and degradation tendencies.",
        tags: ["Driver", "Tyres", "Degradation", "Stints", "Season"],
    },
    {
        id: "t39",
        intent: "Driver Characteristics",
        page: "Driver",
        title: "Lap-time consistency distribution (season)",
        description:
            "Visualises the season-wide distribution of the driver's lap times (clean laps) to highlight consistency, volatility, and outlier behaviour.",
        tags: ["Driver", "Consistency", "Lap Times", "Distribution", "Outliers"],
    },
    {
        id: "t40",
        intent: "Driver Characteristics",
        page: "Driver",
        title: "Race start and recovery (positions gained analysis)",
        description:
            "Summarises how often the driver gains or loses places over races across the season, capturing start effectiveness and in-race recovery ability.",
        tags: ["Driver", "Race Start", "Recovery", "Race Craft", "Positions"],
    },

    // --# Race Page #--
    {
        id: "t24",
        intent: "Team Season Performance",
        page: "Team",
        title: "Team points per race (season trend)",
        description:
            "Shows total points scored by the selected team at each round of a season to identify momentum shifts, upgrade impact, and performance consistency.",
        tags: ["Team", "Season", "Points", "Trend", "Momentum"],
    },
    {
        id: "t25",
        intent: "Team Season Performance",
        page: "Team",
        title: "Finish position distribution (consistency boxplot)",
        description:
            "Displays the distribution of finishing positions for the selected team across a season, highlighting consistency, variability, and race result spread.",
        tags: ["Team", "Finishing Positions", "Consistency", "Distribution", "Season"],
    },
    {
        id: "t26",
        intent: "Team Season Performance",
        page: "Team",
        title: "Grid vs finish scatter (race execution)",
        description:
            "Compares starting grid positions to finishing positions to evaluate whether the team typically gains or loses places during races.",
        tags: ["Team", "Qualifying", "Race Craft", "Positions Gained", "Execution"],
    },
    {
        id: "t27",
        intent: "Team Context & Affinity",
        page: "Team",
        title: "Average points by circuit",
        description:
            "Ranks circuits by the team's average points scored to identify track strengths and weaknesses over a selected time range.",
        tags: ["Team", "Circuit", "Track Performance", "Strengths", "Weaknesses"],
    },
    {
        id: "t28",
        intent: "Team Context & Affinity",
        page: "Team",
        title: "Best and worst circuits table",
        description:
            "Summarises the team's strongest and weakest circuits based on average and total points, including race count for statistical context.",
        tags: ["Team", "Circuit Ranking", "Performance Summary", "Statistics"],
    },
    {
        id: "t29",
        intent: "Team Context & Affinity",
        page: "Team",
        title: "Circuit performance heatmap",
        description:
            "Visualises points scored across circuits and seasons to reveal long-term trends and track-specific performance patterns.",
        tags: ["Team", "Heatmap", "Circuit Trends", "Multi-season", "Performance Patterns"],
    },
    {
        id: "t30",
        intent: "Team Performance Characteristics",
        page: "Team",
        title: "Race pace delta vs field (boxplot)",
        description:
            "Shows the distribution of lap-time deltas between the selected team and the field median to assess true race pace independent of finishing position.",
        tags: ["Team", "Pace", "Lap Time", "Delta", "Performance Analysis"],
    },
    {
        id: "t31",
        intent: "Team Performance Characteristics",
        page: "Team",
        title: "Tyre degradation by compound (stint analysis)",
        description:
            "Plots lap-time evolution within stints by tyre compound to evaluate the team's tyre management and degradation profile.",
        tags: ["Team", "Tyres", "Degradation", "Strategy", "Stints"],
    },

    // --- Pace ---
    {
        id: "t1",
        intent: "Pace",
        page: "Race",
        title: "Driver laptimes scatterplot (consistency/outliers)",
        description:
            "Plots every lap time for selected drivers to quickly spot consistency, traffic-affected laps, and outliers.",
        tags: ["Pace", "Consistency", "Outliers", "Traffic", "Lap-by-lap"],
    },
    {
        id: "t2",
        intent: "Pace",
        page: "Race",
        title: "Driver laptimes distribution (box/violin/hist)",
        description:
            "Shows the overall spread of lap times per driver, making it easy to compare consistency and typical pace at a glance.",
        tags: ["Pace", "Distribution", "Consistency", "Compare drivers"],
    },
    {
        id: "t3",
        intent: "Pace",
        page: "Race",
        title: "Lap time trend (line; rolling avg optional)",
        description:
            "Visualises how lap time changes across the session, useful for spotting long-run pace, tyre drop-off, and performance phases.",
        tags: ["Trend", "Degradation", "Long run", "Stints", "Compare drivers"],
    },
    {
        id: "t4",
        intent: "Pace",
        page: "Race",
        title: "Sector time breakdown (S1/S2/S3 per driver)",
        description:
            "Breaks down performance by sector so users can identify where time is gained or lost on the circuit.",
        tags: ["Sectors", "Strengths/Weaknesses", "Track analysis", "Compare"],
    },
    {
        id: "t5",
        intent: "Pace",
        page: "Race",
        title: "Speed trap comparison (I1/I2/FL/ST)",
        description:
            "Compares speed trap values to highlight top speed differences and where cars are fast along the straights.",
        tags: ["Top speed", "Power", "Straights", "Comparison"],
    },
    {
        id: "t6",
        intent: "Pace",
        page: "Race",
        title: "Team pace comparison (aggregate by team)",
        description:
            "Aggregates lap times by team to compare overall team performance rather than individual drivers.",
        tags: ["Team", "Comparison", "Summary", "Pace"],
    },

    // --- Strategy ---
    {
        id: "t7",
        intent: "Strategy",
        page: "Race",
        title: "Tyre strategy timeline (stints by compound)",
        description:
            "Shows tyre compounds and stints across the race/session to visualise strategies, pit timing, and stint lengths.",
        tags: ["Tyres", "Stints", "Pit strategy", "Timeline", "Race story"],
    },
    {
        id: "t8",
        intent: "Strategy",
        page: "Race",
        title: "Stint length comparison",
        description:
            "Compares how long each stint lasted per driver, revealing one-stops vs two-stops and alternative plans.",
        tags: ["Stints", "Pit windows", "Strategy", "Comparison"],
    },
    {
        id: "t9",
        intent: "Strategy",
        page: "Race",
        title: "Stint average pace (per stint mean/median lap time)",
        description:
            "Summarises pace per stint to compare who was quickest on each tyre run, not just on single laps.",
        tags: ["Stint pace", "Long run", "Degradation", "Strategy"],
    },
    {
        id: "t10",
        intent: "Strategy",
        page: "Race",
        title: "Pit in/out timeline (pit events across laps)",
        description:
            "Marks pit in/out events by lap to show when drivers pitted and how pit sequences shaped track position.",
        tags: ["Pit stops", "Timeline", "Race events", "Undercut/Overcut"],
    },
    {
        id: "t11",
        intent: "Strategy",
        page: "Race",
        title: "Compound performance comparison (pace by compound)",
        description:
            "Compares lap times by tyre compound to see which tyres delivered best pace and how drivers used them.",
        tags: ["Tyres", "Compound", "Pace", "Comparison"],
    },

    // --- Telemetry ---
    {
        id: "t12",
        intent: "Telemetry",
        page: "Race",
        title: "Overlay speed traces of two laps",
        description:
            "Overlays speed traces to compare two laps (two drivers or two attempts) and pinpoint where time was gained.",
        tags: ["Speed trace", "Lap compare", "Delta clues", "Driving style"],
    },
    {
        id: "t13",
        intent: "Telemetry",
        page: "Race",
        title: "Multi-channel lap overlay (speed/throttle/brake)",
        description:
            "Compares driving inputs across a lap by overlaying speed, throttle, and brake to reveal technique differences.",
        tags: ["Throttle", "Brake", "Driving inputs", "Lap compare"],
    },
    {
        id: "t14",
        intent: "Telemetry",
        page: "Race",
        title: "Gear shifts on track",
        description:
            "Maps gear usage around the circuit to show shift points, corner gears, and acceleration zones.",
        tags: ["Gears", "Track map", "Driving technique", "Power delivery"],
    },
    {
        id: "t15",
        intent: "Telemetry",
        page: "Race",
        title: "Speed visualisation on track map",
        description:
            "Colours the racing line by speed to highlight fast sections, braking zones, and minimum-speed corners.",
        tags: ["Track map", "Speed", "Corners", "Braking zones"],
    },
    {
        id: "t16",
        intent: "Telemetry",
        page: "Race",
        title: "Track map (driving line)",
        description:
            "Draws the car's path around the circuit, providing a base layer for other telemetry-based overlays.",
        tags: ["Track map", "Racing line", "Reference"],
    },
    {
        id: "t17",
        intent: "Telemetry",
        page: "Race",
        title: "Driver-ahead proximity (battle/DRS analysis)",
        description:
            "Shows how close a driver was to the car ahead, useful for analysing battles, DRS trains, and overtakes.",
        tags: ["Battles", "DRS", "Proximity", "Racecraft"],
    },

    // --- Positions ---
    {
        id: "t18",
        intent: "Positions",
        page: "Race",
        title: "Position changes during a race (multi-driver)",
        description:
            "Tracks position by lap for multiple drivers to reveal overtakes, pit cycle effects, and big swings.",
        tags: ["Positions", "Overtakes", "Race progression", "Story"],
    },
    {
        id: "t19",
        intent: "Positions",
        page: "Race",
        title: "Driver position timeline (single driver)",
        description:
            "Follows one driver's position across the session to explain their race narrative and key turning points.",
        tags: ["Driver focus", "Race story", "Positions"],
    },
    {
        id: "t20",
        intent: "Positions",
        page: "Race",
        title: "Top-10 position chart (filtered view)",
        description:
            "Shows position changes only for a selected group (e.g., top 10) to keep the chart readable and focused.",
        tags: ["Top 10", "Clarity", "Filtered", "Positions"],
    },

    // --- Season ---
    {
        id: "t21",
        intent: "Season",
        page: "Race",
        title: "Driver standings heatmap (round-by-round)",
        description:
            "Visualises standings across rounds to show momentum, consistency, and turning points in the championship.",
        tags: ["Standings", "Heatmap", "Consistency", "Championship"],
    },
    {
        id: "t22",
        intent: "Season",
        page: "Race",
        title: "Season summary (trend over rounds)",
        description:
            "Shows how points/wins accumulate over a season for drivers or teams, highlighting dominance and close fights.",
        tags: ["Season", "Trend", "Points", "Teams", "Drivers"],
    },
    {
        id: "t23",
        intent: "Season",
        page: "Race",
        title: "Who can still win the WDC?",
        description:
            "Explores championship scenarios by comparing current points with remaining opportunities across the calendar.",
        tags: ["Championship", "Scenarios", "Maths", "Remaining rounds"],
    },
];

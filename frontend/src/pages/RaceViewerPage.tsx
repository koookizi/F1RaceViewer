import { ChevronDownIcon } from "@heroicons/react/20/solid";
import { useState, useEffect, useRef } from "react";
import { DriverAvatar } from "../components/DriverAvatar";
import { StartingGrid } from "../components/StartingGrid";
import { RacePlaybackCircuit } from "../components/RacePlaybackCircuit";
import { RacePlaybackLeaderboard } from "../components/RacePlaybackLeaderboard";
import { RacePlaybackHeader } from "../components/RacePlaybackHeader";
import { RacePlaybackRaceControl } from "../components/RacePlaybackRaceControl";
import { PlaybackControls } from "../components/PlaybackControls";
import type {
    PlaybackData,
    LeaderboardApiResponse,
    WeatherApiResponse,
    RaceControlApiResponse,
    TeamRadioApiResponse,
    VRApiResponse,
} from "../types";
import { teamBgByDriver } from "../helpers/team_colour";
import { RacePlaybackTeamRadio } from "../components/RacePlaybackTeamRadio";
import { RacePlaybackCarData } from "../components/RacePlaybackCarData";
import { VRBuilderBuildControls } from "../components/VRBuilderBuildControls";
import { VRBuilderLivePreview } from "../components/VRBuilderLivePreview";
import { VRBuilderInsightsReports } from "../components/VRBuilderInsightsReports";
import type { MultiSelectOption } from "../components/MultiSelect";
import { ChartCard, type ChartResponse } from "../components/ChartCard";

export interface Result {
    position: number;
    driverNumber: string;
    abbreviation: string;
    name: string;
    team: string;
    team_color: string;
    headshot_url: string;
    country_code: string;
    q1: string | null;
    q2: string | null;
    q3: string | null;
    bestLapTime: string | null;
    lastLapTime: string | null;
    status: string;
    numberOfLaps: number;
    points: number;
    gridPos: number;
}

export function RaceViewerPage() {
    // -- Race selection
    const [yearOptions, setYearOptions] = useState<string[]>([]);
    const [selectedYear, setSelectedYear] = useState<string>("");
    const [countryOptions, setCountryOptions] = useState<string[]>([]);
    const [selectedCountry, setSelectedCountry] = useState<string>("");
    const [sessionsOptions, setSessionsOptions] = useState<string[]>([]);
    const [selectedSession, setSelectedSession] = useState<string>("");
    const [searchButton, setSearchButton] = useState(false);
    const [showRaceSelection, setShowRaceSelection] = useState(true);

    // -- Summary
    const [circuitName, setCircuitName] = useState("");
    const [results, setResults] = useState<Result[]>([]);
    const [loadingResults, setLoadingResults] = useState(false);
    const [showResultsBox, setShowResultsBox] = useState(false);
    const [showStartGrid, setShowStartGrid] = useState(false);
    const raceSessionsWithGridPos = [
        "Race",
        "Sprint",
        "Sprint Shootout",
        "Sprint Qualifying",
    ];

    // -- Tabs
    const [activeTab, setActiveTab] = useState<
        "summary" | "playback" | "vrbuilder" | ""
    >("");
    const [showTabs, setShowTabs] = useState(false);

    const [showSummarySection, setShowSummarySection] = useState(false);
    const [showRacePlayBackSection, setShowRacePlayBackSection] =
        useState(false);
    const [showVRBuilderSection, setShowVRBuilderSection] = useState(false);

    // -- Race Playback
    const [currentTime, setCurrentTime] = useState(0);
    const [data, setData] = useState<PlaybackData | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [speedMultiplier, setSpeedMultiplier] = useState(1);
    const [sessionStart, setSessionStart] = useState("");
    const [selectedDriver, setSelectedDriver] = useState<number | null>(null);
    const [teamRadioAutoplay, setTeamRadioAutoplay] = useState(false);
    const [isScrubbing, setIsScrubbing] = useState(false);
    const [teamRadioAutoplayToken, setTeamRadioAutoplayToken] = useState(0);

    const [leaderboardData, setLeaderboardData] =
        useState<LeaderboardApiResponse | null>(null);

    const [weather, setWeather] = useState<WeatherApiResponse | null>(null);

    const [raceControlData, setRaceControlData] = useState<
        RaceControlApiResponse[] | null
    >(null);

    const [teamRadioData, setTeamRadioData] = useState<
        TeamRadioApiResponse[] | null
    >(null);

    const frameRef = useRef<number | null>(null);
    const lastTimestampRef = useRef<number | null>(null);

    // -- VR Builder
    const stringsToOptions = (items: string[]): MultiSelectOption[] =>
        items.map((value) => ({
            id: value,
            label: value,
        }));

    const [DRIVER_OPTIONS, setDRIVER_OPTIONS] = useState<MultiSelectOption[]>(
        []
    );
    const [TEAM_OPTIONS, setTEAM_OPTIONS] = useState<MultiSelectOption[]>([]);
    const [previewChart, setPreviewChart] = useState<ChartResponse | null>(
        null
    );
    const [reportBlocks, setReportBlocks] = useState<ChartResponse[]>([]);
    const [chartLoading, setChartLoading] = useState(false);

    // Animation loop (safe: no nested setState)
    const isPlayingRef = useRef(isPlaying);
    const speedRef = useRef(speedMultiplier);
    const dataRef = useRef<PlaybackData | null>(data);
    const simTimeRef = useRef<number>(0); // authoritative time
    const lastUiCommitRef = useRef<number>(0); // last timestamp we set React state

    const setCurrentTimeSynced = (value: number) => {
        simTimeRef.current = value; // keep RAF time in sync
        setCurrentTime(value); // update UI
    };

    useEffect(() => {
        isPlayingRef.current = isPlaying;
    }, [isPlaying]);

    useEffect(() => {
        speedRef.current = speedMultiplier;
    }, [speedMultiplier]);

    useEffect(() => {
        dataRef.current = data;
    }, [data]);

    // Animation loop (throttled to avoid max-depth + lag)
    useEffect(() => {
        // Always cancel any existing RAF before deciding what to do (StrictMode-safe)
        if (frameRef.current !== null) {
            cancelAnimationFrame(frameRef.current);
            frameRef.current = null;
        }
        lastTimestampRef.current = null;

        if (!isPlaying || !data) return;

        const raceDuration = data.raceDuration;

        const tick = (timestamp: number) => {
            // stop if paused while a frame was in-flight
            if (!isPlaying) {
                frameRef.current = null;
                lastTimestampRef.current = null;
                return;
            }

            if (lastTimestampRef.current == null) {
                lastTimestampRef.current = timestamp;
            }

            const deltaReal = (timestamp - lastTimestampRef.current) / 1000;
            lastTimestampRef.current = timestamp;

            // advance simulation time in a ref (not state)
            const deltaSim = deltaReal * speedMultiplier;
            simTimeRef.current = Math.min(
                simTimeRef.current + deltaSim,
                raceDuration
            );

            const reachedEnd = simTimeRef.current >= raceDuration;

            // Commit UI state at most ~30fps (every 33ms) to reduce rerenders/effects
            if (timestamp - lastUiCommitRef.current >= 33 || reachedEnd) {
                lastUiCommitRef.current = timestamp;
                setCurrentTime(simTimeRef.current);
            }

            if (reachedEnd) {
                setIsPlaying(false);
                frameRef.current = null;
                lastTimestampRef.current = null;
                return;
            }

            frameRef.current = requestAnimationFrame(tick);
        };

        frameRef.current = requestAnimationFrame(tick);

        return () => {
            if (frameRef.current !== null) {
                cancelAnimationFrame(frameRef.current);
                frameRef.current = null;
            }
            lastTimestampRef.current = null;
        };
    }, [isPlaying, speedMultiplier, data, setCurrentTime, setIsPlaying]);

    // Prints selected driver (for debug)
    useEffect(() => {
        console.log("Selected driver:", selectedDriver);
    }, [selectedDriver]);

    // Handles Summary section
    useEffect(() => {
        if (showSummarySection) {
            setShowResultsBox(true);
            setShowStartGrid(raceSessionsWithGridPos.includes(selectedSession));
        }
    }, [showSummarySection]);

    // Handles tabs
    useEffect(() => {
        switch (activeTab) {
            case "summary":
                setShowSummarySection(true);
                setShowRacePlayBackSection(false);
                setShowVRBuilderSection(false);
                break;

            case "playback":
                setShowSummarySection(false);
                setShowRacePlayBackSection(true);
                setTeamRadioAutoplayToken(1);
                setShowVRBuilderSection(false);
                break;

            case "vrbuilder":
                setShowSummarySection(false);
                setShowRacePlayBackSection(false);
                setShowVRBuilderSection(true);
                break;

            default:
                setShowSummarySection(false);
                setShowRacePlayBackSection(false);
                setShowVRBuilderSection(false);
                break;
        }
    }, [activeTab, searchButton]);

    // When search button is pressed
    const handleSearch = () => {
        if (!selectedYear || !selectedCountry || !selectedSession) return;

        setShowTabs(true);
        setActiveTab("summary");
        setSearchButton(true);
        setLoadingResults(true);
        setShowRaceSelection(false);

        // Fetches VR data
        console.log("Fetching VR data");
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/vr/`
        )
            .then((res) => res.json())
            .then((json: VRApiResponse) => {
                console.log("VR JSON:", json);
                const driverOpts = stringsToOptions(json.drivers);
                const teamOpts = stringsToOptions(json.teams);

                setDRIVER_OPTIONS(driverOpts);
                setTEAM_OPTIONS(teamOpts);
            })
            .catch((err) => {
                console.error("Failed to load VR data", err);
            });

        // Fetches results + starting grid data
        if (raceSessionsWithGridPos.includes(selectedSession)) {
            setShowStartGrid(true);
        }

        console.log("Fetching summary results data");
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/result/`
        )
            .then((res) => res.json())
            .then((data: { results: Result[] }) => {
                setResults(data.results);
                console.log("Summary results JSON:", data);
            })
            .catch((err) => {
                console.error("Failed to load results", err);
            })
            .finally(() => {
                setLoadingResults(false);
            });

        // Fetches playback data
        console.log("Fetching playback data");
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${encodeURIComponent(
                selectedCountry
            )}/${encodeURIComponent(selectedSession)}/playback/`
        )
            .then((res) => res.json())
            .then((json: PlaybackData) => {
                setData(json);
                setCurrentTime(json.playbackControlOffset);
                simTimeRef.current = json.playbackControlOffset;
                setIsPlaying(false);
                setSessionStart(json.sessionStart);
                console.log("Playback JSON:", json);
            })
            .catch((err) => console.error("Failed to load playback", err));

        // Fetches leaderboard data
        console.log("Fetching leaderboard data");
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/leaderboard/`
        )
            .then((res) => res.json())
            .then((json: LeaderboardApiResponse) => {
                console.log("Leaderboard JSON:", json);
                setLeaderboardData(json);
            })
            .catch((err) => {
                console.error("Failed to load leaderboard data", err);
            });

        // Fetches weather data
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/weather/`
        )
            .then((res) => res.json())
            .then((json: WeatherApiResponse) => {
                console.log("Weather JSON:", json);
                setWeather(json);
            })
            .catch((err) => {
                console.error("Failed to load weather data", err);
            });

        // Fetches race control data
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/racecontrol/`
        )
            .then((res) => res.json())
            .then((json: RaceControlApiResponse[]) => {
                console.log("Race control JSON:", json);
                setRaceControlData(json);
            })
            .catch((err) => {
                console.error("Failed to load race control data", err);
            });

        // Fetches team radio data
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/teamradio/`
        )
            .then((res) => res.json())
            .then((json: TeamRadioApiResponse[]) => {
                console.log("Team radio JSON:", json);
                setTeamRadioData(json);
            })
            .catch((err) => {
                console.error("Failed to load team radio data", err);
            });
    };

    // Whenever race selection is touched, hide everything to restart
    useEffect(() => {
        setShowTabs(false);
        setShowSummarySection(false);
        setShowRacePlayBackSection(false);
        setShowVRBuilderSection(false);
    }, [selectedYear, selectedCountry, selectedSession]);

    // Gets years
    useEffect(() => {
        fetch("http://localhost:8000/api/seasons_years/")
            .then((res) => res.json())
            .then((data) => setYearOptions(data.years.map(String)))
            .catch(console.error);
    }, []);

    // Gets countries
    useEffect(() => {
        if (!selectedYear) {
            setCountryOptions([]);
            setSelectedCountry("");
            return;
        }
        fetch(`http://localhost:8000/api/seasons/${selectedYear}/countries/`)
            .then((res) => res.json())
            .then((data: { countries: string[] }) => {
                setCountryOptions(data.countries);
            })
            .catch((err) => {
                console.error("Failed to load countries", err);
            })
            .finally(() => {
                setSelectedCountry("");
            });
    }, [selectedYear]); // Basically means, if selectedYear changes, then this block executes.

    // Gets sessions
    useEffect(() => {
        if (!selectedCountry) {
            setSessionsOptions([]);
            setSelectedSession("");
            return;
        }
        fetch(
            `http://localhost:8000/api/seasons/${selectedYear}/${selectedCountry}/sessions/`
        )
            .then((res) => res.json())
            .then((data: { sessions: string[] }) => {
                setSessionsOptions(data.sessions);
            })
            .catch((err) => {
                console.error("Failed to load sessions", err);
            })
            .finally(() => {
                setSelectedSession("");
            });
    }, [selectedCountry]);

    // Get circuit
    useEffect(() => {
        if (!searchButton) {
            return;
        }
        fetch(
            `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/circuit/`
        )
            .then((res) => res.json())
            .then((data) => {
                setCircuitName(data.circuit);
            })
            .catch((err) => console.error("Error fetching circuit:", err))
            .finally(() => {
                setSearchButton(false);
            });
    }, [searchButton]);

    const sortedResults = [...results].sort((a, b) => a.position - b.position);

    return (
        <>
            {/* Race Selection Section */}
            {showRaceSelection && (
                <div className="h-full grid place-items-center">
                    {/* Race selection */}
                    <div className="card card-border bg-base-200 w-200">
                        <div className="card-body">
                            <h2 className="card-title">Race Selection</h2>
                            <div className="card-actions justify-start">
                                {/* Year dropdown */}
                                <div className="dropdown">
                                    <div
                                        tabIndex={0}
                                        role="button"
                                        className="btn flex items-center gap-2 bg-base-100"
                                    >
                                        {selectedYear || "Select Year"}
                                        <ChevronDownIcon
                                            aria-hidden="true"
                                            className="size-5 opacity-70"
                                        />
                                    </div>

                                    <ul
                                        tabIndex={0}
                                        className="dropdown-content menu bg-base-100 rounded-box z-10 w-56 shadow max-h-96 overflow-y-auto"
                                    >
                                        {yearOptions.map((year) => (
                                            <li key={year}>
                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        setSelectedYear(year)
                                                    }
                                                >
                                                    {year}
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Country dropdown */}
                                {selectedYear && (
                                    <div className="dropdown">
                                        <div
                                            tabIndex={0}
                                            role="button"
                                            className="btn flex items-center gap-2 bg-base-100"
                                        >
                                            {selectedCountry ||
                                                "Select Country"}
                                            <ChevronDownIcon
                                                aria-hidden="true"
                                                className="size-5 opacity-70"
                                            />
                                        </div>

                                        <ul
                                            tabIndex={0}
                                            className="dropdown-content menu bg-base-100 rounded-box z-10 w-56 shadow max-h-96 overflow-y-auto"
                                        >
                                            {countryOptions.map((country) => (
                                                <li key={country}>
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            setSelectedCountry(
                                                                country
                                                            )
                                                        }
                                                    >
                                                        {country}
                                                    </button>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Sessions dropdown */}
                                {selectedCountry && (
                                    <div className="dropdown">
                                        <div
                                            tabIndex={0}
                                            role="button"
                                            className="btn flex items-center gap-2 bg-base-100"
                                        >
                                            {selectedSession ||
                                                "Select Session"}
                                            <ChevronDownIcon
                                                aria-hidden="true"
                                                className="size-5 opacity-70"
                                            />
                                        </div>

                                        <ul
                                            tabIndex={0}
                                            className="dropdown-content menu bg-base-100 rounded-box z-10 w-56 shadow max-h-96 overflow-y-auto"
                                        >
                                            {sessionsOptions.map((session) => (
                                                <li key={session}>
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            setSelectedSession(
                                                                session
                                                            )
                                                        }
                                                    >
                                                        {session}
                                                    </button>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {selectedSession && (
                                    <button
                                        className="btn ms-5 bg-base-300"
                                        onClick={() => {
                                            handleSearch();
                                        }}
                                    >
                                        Search
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* -- Main session section -- */}
            {/* Tabs */}
            {showTabs && (
                <div role="tablist" className="tabs tabs-box">
                    <button
                        role="tab"
                        className={`tab ${
                            activeTab === "summary" ? "tab-active" : ""
                        }`}
                        onClick={() => setActiveTab("summary")}
                    >
                        Summary
                    </button>

                    <button
                        role="tab"
                        className={`tab ${
                            activeTab === "playback" ? "tab-active" : ""
                        }`}
                        onClick={() => setActiveTab("playback")}
                    >
                        Race Playback
                    </button>

                    <button
                        role="tab"
                        className={`tab ${
                            activeTab === "vrbuilder" ? "tab-active" : ""
                        }`}
                        onClick={() => setActiveTab("vrbuilder")}
                    >
                        Visualisation and Report Builder
                    </button>
                </div>
            )}

            {/* -- Race Visualisation and Report Builder section */}
            <div className="">
                {showVRBuilderSection && (
                    <>
                        <div className="mt-2">
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-2">
                                <div className="md:col-span-6">
                                    {/* Build controls */}
                                    <VRBuilderBuildControls
                                        TEAM_OPTIONS={TEAM_OPTIONS}
                                        DRIVER_OPTIONS={DRIVER_OPTIONS}
                                        setPreviewChart={setPreviewChart}
                                        selectedYear={selectedYear}
                                        selectedSession={selectedSession}
                                        selectedCountry={selectedCountry}
                                        setChartLoading={setChartLoading}
                                    />
                                </div>
                                <div className="md:col-span-6">
                                    {/* Live preview */}
                                    <VRBuilderLivePreview
                                        setReportBlocks={setReportBlocks}
                                        chartLoading={chartLoading}
                                        previewChart={previewChart}
                                    />
                                </div>
                                <div className="md:col-span-12">
                                    {/* Insights and Reports */}
                                    <VRBuilderInsightsReports
                                        reportBlocks={reportBlocks}
                                        setReportBlocks={setReportBlocks}
                                    />
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* -- Race Playback section */}
            <div className="">
                {showRacePlayBackSection && (
                    <>
                        <div className="mt-2 pb-24">
                            {/* Race playback circuit */}
                            <PlaybackControls
                                data={data}
                                currentTime={currentTime}
                                sessionStart={sessionStart}
                                setCurrentTime={setCurrentTimeSynced}
                                isPlaying={isPlaying}
                                setIsPlaying={setIsPlaying}
                                speedMultiplier={speedMultiplier}
                                setSpeedMultiplier={setSpeedMultiplier}
                                setIsScrubbing={setIsScrubbing}
                                triggerTeamRadioAutoplay={() =>
                                    setTeamRadioAutoplayToken((t) => t + 1)
                                }
                            />

                            <div className="grid grid-cols-1 md:grid-cols-12 gap-2">
                                <div className="md:col-span-12">
                                    {/* Race playback weather info */}
                                    <RacePlaybackHeader
                                        weatherData={weather}
                                        playbackData={data}
                                        currentTime={currentTime}
                                        sessionStart={sessionStart}
                                        circuitName={circuitName}
                                        selectedSession={selectedSession}
                                        selectedYear={selectedYear}
                                    />
                                </div>
                                <div className="md:col-span-8">
                                    {/* Race playback leaderboard */}
                                    <RacePlaybackLeaderboard
                                        leaderboardData={leaderboardData}
                                        currentTime={currentTime}
                                        selectedDriver={selectedDriver}
                                        setSelectedDriver={setSelectedDriver}
                                    />
                                </div>
                                <div className="grid col-span-4 grid-cols-1 gap-2 self-start h-fit">
                                    <div className="col-span-1">
                                        {/* Race playback circuit */}
                                        <RacePlaybackCircuit
                                            data={data}
                                            currentTime={currentTime}
                                            leaderboardData={leaderboardData}
                                            selectedDriver={selectedDriver}
                                        />
                                    </div>
                                    <div className="col-span-1">
                                        {/* Driver data */}
                                        <RacePlaybackCarData
                                            leaderboardData={leaderboardData}
                                            currentTime={currentTime}
                                            selectedDriver={selectedDriver}
                                        />
                                    </div>
                                </div>
                                <div className="md:col-span-6">
                                    {/* Race control */}
                                    <RacePlaybackRaceControl
                                        raceControlData={raceControlData}
                                        currentTime={currentTime}
                                    />
                                </div>
                                <div className="md:col-span-6">
                                    {/* Race control */}
                                    <RacePlaybackTeamRadio
                                        teamRadioData={teamRadioData}
                                        teamRadioAutoplay={teamRadioAutoplay}
                                        setTeamRadioAutoplay={
                                            setTeamRadioAutoplay
                                        }
                                        leaderboardData={leaderboardData}
                                        currentTime={currentTime}
                                        isScrubbing={isScrubbing}
                                        teamRadioAutoplayToken={
                                            teamRadioAutoplayToken
                                        }
                                    />
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* -- Summary section */}
            <div className="">
                {showSummarySection && (
                    <>
                        <div className="mt-2">
                            <div className="grid grid-cols-3 gap-2">
                                <div className="col-span-3">
                                    {/* Results */}
                                    {showResultsBox && (
                                        <>
                                            <div className="card card-border bg-base-100 w-auto">
                                                <div className="card-body">
                                                    <h2 className="card-title">
                                                        {circuitName.toUpperCase()}{" "}
                                                        {selectedYear} GRAND
                                                        PRIX -{" "}
                                                        {selectedSession.toUpperCase()}
                                                    </h2>
                                                    <p>
                                                        Results of the selected
                                                        session.
                                                        <br />
                                                        <em>
                                                            Note: Certain
                                                            sessions,
                                                            particularly older
                                                            sessions, may not
                                                            have lap data
                                                            available.
                                                        </em>
                                                    </p>

                                                    <div className="overflow-x-auto">
                                                        <table className="table [&_td]:py-2">
                                                            {!loadingResults && (
                                                                <thead>
                                                                    <>
                                                                        {selectedSession.includes(
                                                                            "Practice"
                                                                        ) && (
                                                                            <tr>
                                                                                <th>
                                                                                    Pos
                                                                                </th>
                                                                                <th>
                                                                                    Driver
                                                                                    No.
                                                                                </th>
                                                                                <th></th>
                                                                                <th>
                                                                                    Driver
                                                                                </th>
                                                                                <th>
                                                                                    Team
                                                                                </th>
                                                                                <th>
                                                                                    Time
                                                                                </th>
                                                                                <th>
                                                                                    Laps
                                                                                </th>
                                                                            </tr>
                                                                        )}

                                                                        {(selectedSession.includes(
                                                                            "Qualifying"
                                                                        ) ||
                                                                            selectedSession.includes(
                                                                                "Shootout"
                                                                            )) && (
                                                                            <tr>
                                                                                <th>
                                                                                    Pos
                                                                                </th>
                                                                                <th>
                                                                                    Driver
                                                                                    No.
                                                                                </th>
                                                                                <th></th>
                                                                                <th>
                                                                                    Driver
                                                                                </th>
                                                                                <th>
                                                                                    Team
                                                                                </th>
                                                                                <th>
                                                                                    Q1
                                                                                </th>
                                                                                <th>
                                                                                    Q2
                                                                                </th>
                                                                                <th>
                                                                                    Q3
                                                                                </th>
                                                                                <th>
                                                                                    Laps
                                                                                </th>
                                                                            </tr>
                                                                        )}

                                                                        {(selectedSession.includes(
                                                                            "Race"
                                                                        ) ||
                                                                            selectedSession.includes(
                                                                                "Sprint"
                                                                            )) && (
                                                                            <tr>
                                                                                <th>
                                                                                    Pos
                                                                                </th>
                                                                                <th>
                                                                                    Driver
                                                                                    No.
                                                                                </th>
                                                                                <th></th>
                                                                                <th>
                                                                                    Driver
                                                                                </th>
                                                                                <th>
                                                                                    Team
                                                                                </th>
                                                                                <th>
                                                                                    Laps
                                                                                </th>
                                                                                <th>
                                                                                    Best
                                                                                    Lap
                                                                                    Time
                                                                                </th>
                                                                                <th>
                                                                                    Last
                                                                                    Lap
                                                                                    Time
                                                                                </th>
                                                                                <th>
                                                                                    Points
                                                                                </th>
                                                                                <th>
                                                                                    Status
                                                                                </th>
                                                                            </tr>
                                                                        )}
                                                                    </>
                                                                </thead>
                                                            )}
                                                            <tbody>
                                                                {loadingResults ? (
                                                                    <tr>
                                                                        <td
                                                                            colSpan={
                                                                                7
                                                                            }
                                                                            className="p-0"
                                                                        >
                                                                            <div className="skeleton h-32 w-auto"></div>
                                                                        </td>
                                                                    </tr>
                                                                ) : (
                                                                    <>
                                                                        {selectedSession.includes(
                                                                            "Practice"
                                                                        ) &&
                                                                            sortedResults.map(
                                                                                (
                                                                                    r
                                                                                ) => (
                                                                                    <tr
                                                                                        key={`${r.driverNumber}-${r.position}`}
                                                                                        style={{
                                                                                            backgroundColor:
                                                                                                teamBgByDriver(
                                                                                                    leaderboardData,
                                                                                                    Number(
                                                                                                        r.driverNumber
                                                                                                    )
                                                                                                ) ??
                                                                                                "transparent",
                                                                                        }}
                                                                                    >
                                                                                        <td>
                                                                                            {
                                                                                                r.position
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.driverNumber
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            <div className="flex items-center gap-3">
                                                                                                <DriverAvatar
                                                                                                    name={
                                                                                                        r.name
                                                                                                    }
                                                                                                    headshotUrl={
                                                                                                        r.headshot_url
                                                                                                    }
                                                                                                />
                                                                                            </div>
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.name
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.team
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.bestLapTime
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.numberOfLaps
                                                                                            }
                                                                                        </td>
                                                                                    </tr>
                                                                                )
                                                                            )}

                                                                        {(selectedSession.includes(
                                                                            "Qualifying"
                                                                        ) ||
                                                                            selectedSession.includes(
                                                                                "Shootout"
                                                                            )) &&
                                                                            sortedResults.map(
                                                                                (
                                                                                    r
                                                                                ) => (
                                                                                    <tr
                                                                                        key={`${r.driverNumber}-${r.position}`}
                                                                                        style={{
                                                                                            backgroundColor:
                                                                                                teamBgByDriver(
                                                                                                    leaderboardData,
                                                                                                    Number(
                                                                                                        r.driverNumber
                                                                                                    )
                                                                                                ) ??
                                                                                                "transparent",
                                                                                        }}
                                                                                    >
                                                                                        <td>
                                                                                            {
                                                                                                r.position
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.driverNumber
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            <div className="flex items-center gap-3">
                                                                                                <DriverAvatar
                                                                                                    name={
                                                                                                        r.name
                                                                                                    }
                                                                                                    headshotUrl={
                                                                                                        r.headshot_url
                                                                                                    }
                                                                                                />
                                                                                            </div>
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.name
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.team
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.q1
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.q2
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.q3
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.bestLapTime
                                                                                            }
                                                                                        </td>
                                                                                    </tr>
                                                                                )
                                                                            )}

                                                                        {(selectedSession.includes(
                                                                            "Race"
                                                                        ) ||
                                                                            selectedSession.includes(
                                                                                "Sprint"
                                                                            )) &&
                                                                            sortedResults.map(
                                                                                (
                                                                                    r
                                                                                ) => (
                                                                                    <tr
                                                                                        key={`${r.driverNumber}-${r.position}`}
                                                                                        style={{
                                                                                            backgroundColor:
                                                                                                teamBgByDriver(
                                                                                                    leaderboardData,
                                                                                                    Number(
                                                                                                        r.driverNumber
                                                                                                    )
                                                                                                ) ??
                                                                                                "transparent",
                                                                                        }}
                                                                                    >
                                                                                        <td>
                                                                                            {
                                                                                                r.position
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.driverNumber
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            <div className="flex items-center gap-3">
                                                                                                <DriverAvatar
                                                                                                    name={
                                                                                                        r.name
                                                                                                    }
                                                                                                    headshotUrl={
                                                                                                        r.headshot_url
                                                                                                    }
                                                                                                />
                                                                                            </div>
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.name
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.team
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.numberOfLaps
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.bestLapTime
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.lastLapTime
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.points
                                                                                            }
                                                                                        </td>
                                                                                        <td>
                                                                                            {
                                                                                                r.status
                                                                                            }
                                                                                        </td>
                                                                                    </tr>
                                                                                )
                                                                            )}
                                                                    </>
                                                                )}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>
                                <div className="col-span-3">
                                    {/* Starting grid */}
                                    {showStartGrid && (
                                        <div className="card card-border bg-base-100">
                                            <div className="card-body">
                                                <h2 className="card-title">
                                                    STARTING GRID
                                                </h2>
                                                <div className="mt-2">
                                                    {loadingResults ? (
                                                        <div className="skeleton h-32 w-auto"></div>
                                                    ) : (
                                                        <StartingGrid
                                                            results={results}
                                                        />
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </>
    );
}

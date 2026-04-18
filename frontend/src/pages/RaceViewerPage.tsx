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
    blockState,
} from "../types";
import { teamBgByDriver } from "../helpers/team_colour";
import { RacePlaybackTeamRadio } from "../components/RacePlaybackTeamRadio";
import { RacePlaybackCarData } from "../components/RacePlaybackCarData";
import { VRBuilderBuildControls } from "../components/VRBuilderBuildControls";
import { VRBuilderLivePreview } from "../components/VRBuilderLivePreview";
import { VRBuilderInsightsReports } from "../components/VRBuilderInsightsReports";
import type { MultiSelectOption } from "../components/MultiSelect";
import { type ChartResponse } from "../components/ChartCard";
import { useToast } from "../components/ToastContext";
import { fetchJson } from "../helpers/api";
import { BlockedCard } from "../components/BlockedCard";
import { useLoadingTracker } from "../helpers/loading";
import { LoadingOverlay } from "../components/LoadingOverlay";

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
    // -- Toast
    const toast = useToast();

    // -- Loading tracker
    const {
        startLoading,
        stopLoading,
        progress,
        pendingIds,
        isLoading
    } = useLoadingTracker();

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
    const [showHero, setShowHero] = useState(false);
    const [circuitName, setCircuitName] = useState("");
    const [results, setResults] = useState<Result[]>([]);
    const [showResultsBox, setShowResultsBox] = useState(false);
    const [showStartGrid, setShowStartGrid] = useState(false);
    const raceSessionsWithGridPos = ["Race", "Sprint", "Sprint Shootout", "Sprint Qualifying"];

    // -- Tabs
    const [activeTab, setActiveTab] = useState<"summary" | "playback" | "vrbuilder" | "">("");
    const [showTabs, setShowTabs] = useState(false);

    const [showSummarySection, setShowSummarySection] = useState(false);
    const [showRacePlayBackSection, setShowRacePlayBackSection] = useState(false);
    const [showVRBuilderSection, setShowVRBuilderSection] = useState(false);

    // -- Header
    const [showHeader, setShowHeader] = useState(false);

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

    const [leaderboardData, setLeaderboardData] = useState<LeaderboardApiResponse | null>(null);

    const [weather, setWeather] = useState<WeatherApiResponse | null>(null);

    const [raceControlData, setRaceControlData] = useState<RaceControlApiResponse[] | null>(null);

    const [teamRadioData, setTeamRadioData] = useState<TeamRadioApiResponse[] | null>(null);

    const frameRef = useRef<number | null>(null);
    const lastTimestampRef = useRef<number | null>(null);

    const [blockRacePlayback, setBlockRacePlayback] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockPlaybackControls, setBlockPlaybackControls] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockRacePlaybackHeader, setBlockRacePlaybackHeader] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockRacePlaybackLeaderboard, setBlockRacePlaybackLeaderboard] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockRacePlaybackCircuit, setBlockRacePlaybackCircuit] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockRacePlaybackCarData, setBlockRacePlaybackCarData] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockRacePlaybackRaceControl, setBlockRacePlaybackRaceControl] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockRacePlaybackTeamRadio, setBlockRacePlaybackTeamRadio] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });
    const [blockFULL, setBlockFULL] = useState<blockState>({
        blocked: false,
        reason: "",
        error: "",
    });

    // -- Loading indicator
    useEffect(() => {
        console.log("Progress:", progress + "%");
        console.log("Is Loading:", isLoading);
    }, [progress, isLoading]);

    // -- VR Builder
    const stringsToOptions = (items: string[]): MultiSelectOption[] =>
        items.map((value) => ({
            id: value,
            label: value,
        }));

    const [DRIVER_OPTIONS, setDRIVER_OPTIONS] = useState<MultiSelectOption[]>([]);
    const [TEAM_OPTIONS, setTEAM_OPTIONS] = useState<MultiSelectOption[]>([]);
    const [previewChart, setPreviewChart] = useState<ChartResponse | null>(null);
    const [reportBlocks, setReportBlocks] = useState<ChartResponse[]>([]);
    const [chartLoading, setChartLoading] = useState(false);

    // Animation loop
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

    // Animation loop
    useEffect(() => {
        // Always cancel any existing RAF before deciding what to do
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

            // advance simulation time in a ref
            const deltaSim = deltaReal * speedMultiplier;
            simTimeRef.current = Math.min(simTimeRef.current + deltaSim, raceDuration);

            const reachedEnd = simTimeRef.current >= raceDuration;

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

    useEffect(() => {
        console.log("Selected driver:", selectedDriver);
    }, [selectedDriver]);

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
        setShowRaceSelection(false);
        setShowHeader(true);

        // Handles Race Playback Block
        if (Number(selectedYear) < 2023) {
            setBlockRacePlayback({
                blocked: true,
                reason: "Race Playback only available for races 2023 onwards.",
                error: "",
            });
        }

        // Fetches VR data
        console.log("Fetching VR data");
        startLoading("report builder");
        fetchJson<VRApiResponse>(
            `/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/vr/`,
        )
            .then((json: VRApiResponse) => {
                console.log("VR JSON:", json);
                const driverOpts = stringsToOptions(json.drivers);
                const teamOpts = stringsToOptions(json.teams);

                setDRIVER_OPTIONS(driverOpts);
                setTEAM_OPTIONS(teamOpts);
            })
            .catch((err) => {
                console.error("Failed to load VR data", err);
                toast("Failed to load VR data: " + err.message, "error");
            })
            .finally(() => {                
                stopLoading("report builder");            
            });

        // Fetches results + starting grid data
        startLoading("race results");
        console.log("Fetching summary results data");
        fetchJson<{ results: Result[] }>(
            `/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/result/`,
        )
            .then((data: { results: Result[] }) => {
                setResults(data.results);
                console.log("Summary results JSON:", data);

                if (data.results.length === 0) {
                    setBlockFULL({
                    blocked: true,
                    reason: "No results data available for this session. This session may not have taken place, or data may be missing.",
                    error: "Race not loaded.",
                });
                }

            })
            .catch((err) => {
                console.error("Failed to load results", err);
                toast("Failed to load results: " + err.message, "error");
            })
            .finally(() => {
            
                setShowResultsBox(true);
                if (raceSessionsWithGridPos.includes(selectedSession)) {
                    setShowStartGrid(true);
                }
                stopLoading("race results");
            });

        // Fetches playback data
        startLoading("race playback");
        console.log("Fetching playback data");
        fetchJson<PlaybackData>(
            `/api/session/${selectedYear}/${encodeURIComponent(
                selectedCountry,
            )}/${encodeURIComponent(selectedSession)}/playback/`,
        )
            .then((json: PlaybackData) => {
                setData(json);
                setCurrentTime(json.playbackControlOffset);
                simTimeRef.current = json.playbackControlOffset;
                setIsPlaying(false);
                setSessionStart(json.sessionStart);
                console.log("Playback JSON:", json);
            })
            .catch((err) => {
                console.error("Failed to load playback", err);
                toast("Failed to load playback: " + err.message, "error");
                setBlockRacePlayback({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
                setBlockRacePlaybackHeader({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
                setBlockRacePlaybackCircuit({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
                setBlockPlaybackControls({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
            })
            .finally(() => {                
                stopLoading("race playback");            
            });

        // Fetches leaderboard data
        startLoading("leaderboard");
        console.log("Fetching leaderboard data");
        fetchJson<LeaderboardApiResponse>(
            `/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/leaderboard/`,
        )
            .then((json: LeaderboardApiResponse) => {
                console.log("Leaderboard JSON:", json);
                setLeaderboardData(json);
            })
            .catch((err) => {
                console.error("Failed to load leaderboard data", err);
                toast("Failed to load leaderboard data: " + err.message, "error");
                setBlockRacePlaybackLeaderboard({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
                setBlockRacePlaybackCarData({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
                setBlockRacePlaybackCircuit({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
            })
            .finally(() => {                
                stopLoading("leaderboard");            
            });
            

        // Fetches weather data
        startLoading("weather");
        fetchJson<WeatherApiResponse>(
            `/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/weather/`,
        )
            .then((json: WeatherApiResponse) => {
                console.log("Weather JSON:", json);
                setWeather(json);
            })
            .catch((err) => {
                console.error("Failed to load weather data", err);
                toast("Failed to load weather data: " + err.message, "error");
                setBlockRacePlaybackHeader({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
            })
            .finally(() => {                
                stopLoading("weather");            
            });

        // Fetches race control data
        startLoading("race control");
        fetchJson<RaceControlApiResponse[]>(
            `/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/racecontrol/`,
        )
            .then((json: RaceControlApiResponse[]) => {
                console.log("Race control JSON:", json);
                setRaceControlData(json);
            })
            .catch((err) => {
                console.error("Failed to load race control data", err);
                toast("Failed to load race control data: " + err.message, "error");
                setBlockRacePlaybackRaceControl({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
            })
            .finally(() => {                
                stopLoading("race control");            
            });

        // Fetches team radio data
        startLoading("team radio");
        fetchJson<TeamRadioApiResponse[]>(
            `/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/teamradio/`,
        )
            .then((json: TeamRadioApiResponse[]) => {
                console.log("Team radio JSON:", json);
                setTeamRadioData(json);
            })
            .catch((err) => {
                console.error("Failed to load team radio data", err);
                toast("Failed to load team radio data: " + err.message, "error");
                setBlockRacePlaybackTeamRadio({
                    blocked: true,
                    reason: err.message,
                    error: err.error,
                });
            })
            .finally(() => {                
                stopLoading("team radio");            
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
        fetchJson<{ years: string[] }>("/api/seasons_years/")
            .then((data) => {
                setYearOptions(data.years.map(String));
            })
            .catch((err) => {
                console.error("Failed to load years", err);
                toast("Failed to load years: " + err.message, "error");
            });
    }, []);

    // Gets countries
    useEffect(() => {
        if (!selectedYear) {
            setCountryOptions([]);
            setSelectedCountry("");
            return;
        }
        fetchJson<{ countries: string[] }>(
            `/api/seasons/${selectedYear}/countries/`,
        )
            .then((data: { countries: string[] }) => {
                setCountryOptions(data.countries);
            })
            .catch((err) => {
                console.error("Failed to load countries", err);
                toast("Failed to load countries: " + err.message, "error");
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
        fetchJson<{ sessions: string[] }>(
            `/api/seasons/${selectedYear}/${selectedCountry}/sessions/`,
        )
            .then((data: { sessions: string[] }) => {
                setSessionsOptions(data.sessions);
            })
            .catch((err) => {
                console.error("Failed to load sessions", err);
                toast("Failed to load sessions: " + err.message, "error");
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
        fetchJson<{ circuit: string }>(
            `/api/session/${selectedYear}/${selectedCountry}/circuit/`,
        )
            .then((data) => {
                setCircuitName(data.circuit);
                setShowHero(true);
            })
            .catch((err) => {
                console.error("Error fetching circuit:", err);
                toast("Failed to load circuit data: " + err.message, "error");
            })
            .finally(() => {
                setSearchButton(false);
            });
    }, [searchButton]);

    const sortedResults = [...results].sort((a, b) => a.position - b.position);

    return (
        <>
            {/* Race Selection Section */}
            {showRaceSelection && (
                <div className="h-full flex items-center justify-center">
                    <div className="flex flex-col items-center">
                        {/* Race selection */}
                        <h1 className="text-center text-5xl font-medium mb-2">Select a Race</h1>
                        <p className="text-md text-slate-500 mb-8 text-center">
                            Explore and visualise data from past Formula 1 sessions.
                        </p>

                        <div className="card card-border bg-base-200 w-80 md:w-150">
                            <div className="card-body">
                                <div className="card-actions justify-center">
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
                                                        onClick={() => setSelectedYear(year)}
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
                                                {selectedCountry || "Select Country"}
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
                                                                setSelectedCountry(country)
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
                                                {selectedSession || "Select Session"}
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
                                                                setSelectedSession(session)
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

                        <p className="text-sm text-slate-500 mt-8 text-center">
                            Due to data availability, Race Playback is only available for 2023 to 2025 seasons.
                        </p>
                    </div>
                </div>
            )}

            {/* -- Main session section -- */}
            {/* Header */}
            {showHeader && (
                <div className="flex items-center justify-between w-full mb-2">
                    <button
                        className="btn bg-base-100 flex items-center gap-2"
                        onClick={() => {
                            window.location.href = "/race-viewer";
                        }}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={2}
                            stroke="currentColor"
                            className="w-5 h-5"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M15.75 19.5L8.25 12l7.5-7.5"
                            />
                        </svg>

                        <span>Find another Race</span>
                    </button>

                    <div className="text-lg font-semibold">Race Viewer</div>
                </div>
            )}

            {blockFULL.blocked ? (
                <div className="flex items-center justify-center py-24">
                    <BlockedCard
                        title="Race not available"
                        reason={blockFULL.reason}
                    />
                </div>
            ) : (
                <>
                    <LoadingOverlay loading={isLoading} progress={progress} label={`Fetching ${pendingIds[0]} data`} />

            {/* Tabs */}
            {showTabs && (
                <div role="tablist" className="tabs tabs-box">
                    <button
                        role="tab"
                        className={`tab ${activeTab === "summary" ? "tab-active" : ""}`}
                        onClick={() => setActiveTab("summary")}
                    >
                        Summary
                    </button>

                    <button
                        role="tab"
                        className={`tab ${activeTab === "playback" ? "tab-active" : ""}`}
                        onClick={() => setActiveTab("playback")}
                    >
                        Race Playback
                    </button>

                    <button
                        role="tab"
                        className={`tab ${activeTab === "vrbuilder" ? "tab-active" : ""}`}
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
                                        page={"Race"}
                                        TEAM_OPTIONS={TEAM_OPTIONS}
                                        DRIVER_OPTIONS={DRIVER_OPTIONS}
                                        setPreviewChart={setPreviewChart}
                                        selectedYear={selectedYear}
                                        selectedSession={selectedSession}
                                        selectedCountry={selectedCountry}
                                        setChartLoading={setChartLoading}
                                        chartLoading={chartLoading}
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
            <div>
                {showRacePlayBackSection && (
                    <>
                        {blockRacePlayback.blocked ? (
                            <div className="flex items-center justify-center py-24">
                                <BlockedCard
                                    title="Race Playback Disabled"
                                    reason={blockRacePlayback.reason}
                                />
                            </div>
                        ) : (
                            <div className="mt-2 pb-24">
                                {/* Race playback controls */}
                                {blockPlaybackControls.blocked ? (
                                    <BlockedCard
                                        title="Race Playback Controls Disabled"
                                        reason={blockPlaybackControls.reason}
                                    />
                                ) : (
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
                                )}

                                <div className="grid grid-cols-1 md:grid-cols-12 gap-2">
                                    <div className="md:col-span-12">
                                        {blockRacePlaybackHeader.blocked ? (
                                            <BlockedCard
                                                title="Race Playback Header Disabled"
                                                reason={blockRacePlaybackHeader.reason}
                                            />
                                        ) : (
                                            <RacePlaybackHeader
                                                weatherData={weather}
                                                playbackData={data}
                                                currentTime={currentTime}
                                                sessionStart={sessionStart}
                                                circuitName={circuitName}
                                                selectedSession={selectedSession}
                                                selectedYear={selectedYear}
                                            />
                                        )}
                                    </div>

                                    <div className="md:col-span-8">
                                        {blockRacePlaybackLeaderboard.blocked ? (
                                            <BlockedCard
                                                title="Race Playback Leaderboard Disabled"
                                                reason={blockRacePlaybackLeaderboard.reason}
                                            />
                                        ) : (
                                            <RacePlaybackLeaderboard
                                                leaderboardData={leaderboardData}
                                                currentTime={currentTime}
                                                selectedDriver={selectedDriver}
                                                setSelectedDriver={setSelectedDriver}
                                            />
                                        )}
                                    </div>

                                    <div className="grid col-span-4 grid-cols-1 gap-2 self-start h-fit">
                                        {blockRacePlaybackCircuit.blocked ? (
                                            <BlockedCard
                                                title="Race Playback Circuit Disabled"
                                                reason={blockRacePlaybackCircuit.reason}
                                            />
                                        ) : (
                                            <RacePlaybackCircuit
                                                data={data}
                                                currentTime={currentTime}
                                                leaderboardData={leaderboardData}
                                                selectedDriver={selectedDriver}
                                            />
                                        )}

                                        {blockRacePlaybackCarData.blocked ? (
                                            <BlockedCard
                                                title="Race Playback Car Data Disabled"
                                                reason={blockRacePlaybackCarData.reason}
                                            />
                                        ) : (
                                            <RacePlaybackCarData
                                                leaderboardData={leaderboardData}
                                                currentTime={currentTime}
                                                selectedDriver={selectedDriver}
                                            />
                                        )}
                                    </div>

                                    <div className="md:col-span-6">
                                        {blockRacePlaybackRaceControl.blocked ? (
                                            <BlockedCard
                                                title="Race Playback Race Control Disabled"
                                                reason={blockRacePlaybackRaceControl.reason}
                                            />
                                        ) : (
                                            <RacePlaybackRaceControl
                                                raceControlData={raceControlData}
                                                currentTime={currentTime}
                                            />
                                        )}
                                    </div>

                                    <div className="md:col-span-6">
                                        {blockRacePlaybackTeamRadio.blocked ? (
                                            <BlockedCard
                                                title="Race Playback Team Radio Disabled"
                                                reason={blockRacePlaybackTeamRadio.reason}
                                            />
                                        ) : (
                                            <RacePlaybackTeamRadio
                                                teamRadioData={teamRadioData}
                                                teamRadioAutoplay={teamRadioAutoplay}
                                                setTeamRadioAutoplay={setTeamRadioAutoplay}
                                                leaderboardData={leaderboardData}
                                                currentTime={currentTime}
                                                isScrubbing={isScrubbing}
                                                teamRadioAutoplayToken={teamRadioAutoplayToken}
                                            />
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
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
                                    {/* Hero */}
                                    {showHero ? (
                                        <>
                                            <div className="card card-border w-auto h-80 bg-black">
                                                <div className="card-body text-center flex flex-col justify-center items-center">
                                                    <h2 className="card-title text-5xl text-white">
                                                        {circuitName.toUpperCase()} {selectedYear}{" "}
                                                        GRAND PRIX - {selectedSession.toUpperCase()}
                                                    </h2>
                                                    <div className="text-md text-white/80">
                                                        Formula 1 Session
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="skeleton h-32 w-auto"></div>
                                    )}
                                </div>
                                <div className="col-span-3">
                                    {/* Results */}
                                    {showResultsBox ? (
                                        <>
                                            <div className="card card-border bg-base-100 w-auto">
                                                <div className="card-body">
                                                    <h2 className="card-title">RESULTS</h2>
                                                    <p>
                                                        Results of the selected session.
                                                        <br />
                                                        <em>
                                                            Note: Certain sessions, particularly
                                                            older sessions, may not have lap data
                                                            available.
                                                        </em>
                                                    </p>

                                                    <div className="overflow-x-auto">
                                                        <table className="table [&_td]:py-2">
                                                            <thead>
                                                                <>
                                                                    {selectedSession.includes(
                                                                        "Practice",
                                                                    ) && (
                                                                        <tr>
                                                                            <th>Pos</th>
                                                                            <th>Driver No.</th>
                                                                            <th></th>
                                                                            <th>Driver</th>
                                                                            <th>Team</th>
                                                                            <th>Time</th>
                                                                            <th>Laps</th>
                                                                        </tr>
                                                                    )}

                                                                    {(selectedSession.includes(
                                                                        "Qualifying",
                                                                    ) ||
                                                                        selectedSession.includes(
                                                                            "Shootout",
                                                                        )) && (
                                                                        <tr>
                                                                            <th>Pos</th>
                                                                            <th>Driver No.</th>
                                                                            <th></th>
                                                                            <th>Driver</th>
                                                                            <th>Team</th>
                                                                            <th>Q1</th>
                                                                            <th>Q2</th>
                                                                            <th>Q3</th>
                                                                            <th>Laps</th>
                                                                        </tr>
                                                                    )}

                                                                    {(selectedSession.includes(
                                                                        "Race",
                                                                    ) ||
                                                                        selectedSession.includes(
                                                                            "Sprint",
                                                                        )) && (
                                                                        <tr>
                                                                            <th>Pos</th>
                                                                            <th>Driver No.</th>
                                                                            <th></th>
                                                                            <th>Driver</th>
                                                                            <th>Team</th>
                                                                            <th>Laps</th>
                                                                            <th>Best Lap Time</th>
                                                                            <th>Last Lap Time</th>
                                                                            <th>Points</th>
                                                                            <th>Status</th>
                                                                        </tr>
                                                                    )}
                                                                </>
                                                            </thead>
                                                            <tbody>
                                                                {selectedSession.includes(
                                                                    "Practice",
                                                                ) &&
                                                                    sortedResults.map((r) => (
                                                                        <tr
                                                                            key={`${r.driverNumber}-${r.position}`}
                                                                            style={{
                                                                                backgroundColor:
                                                                                    teamBgByDriver(
                                                                                        leaderboardData,
                                                                                        Number(
                                                                                            r.driverNumber,
                                                                                        ),
                                                                                    ) ??
                                                                                    "transparent",
                                                                            }}
                                                                        >
                                                                            <td>{r.position}</td>
                                                                            <td>
                                                                                {r.driverNumber}
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
                                                                            <td>{r.name}</td>
                                                                            <td>{r.team}</td>
                                                                            <td>{r.bestLapTime}</td>
                                                                            <td>
                                                                                {r.numberOfLaps}
                                                                            </td>
                                                                        </tr>
                                                                    ))}

                                                                {(selectedSession.includes(
                                                                    "Qualifying",
                                                                ) ||
                                                                    selectedSession.includes(
                                                                        "Shootout",
                                                                    )) &&
                                                                    sortedResults.map((r) => (
                                                                        <tr
                                                                            key={`${r.driverNumber}-${r.position}`}
                                                                            style={{
                                                                                backgroundColor:
                                                                                    teamBgByDriver(
                                                                                        leaderboardData,
                                                                                        Number(
                                                                                            r.driverNumber,
                                                                                        ),
                                                                                    ) ??
                                                                                    "transparent",
                                                                            }}
                                                                        >
                                                                            <td>{r.position}</td>
                                                                            <td>
                                                                                {r.driverNumber}
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
                                                                            <td>{r.name}</td>
                                                                            <td>{r.team}</td>
                                                                            <td>{r.q1}</td>
                                                                            <td>{r.q2}</td>
                                                                            <td>{r.q3}</td>
                                                                            <td>{r.bestLapTime}</td>
                                                                        </tr>
                                                                    ))}

                                                                {(selectedSession.includes(
                                                                    "Race",
                                                                ) ||
                                                                    selectedSession.includes(
                                                                        "Sprint",
                                                                    )) &&
                                                                    sortedResults.map((r) => (
                                                                        <tr
                                                                            key={`${r.driverNumber}-${r.position}`}
                                                                            style={{
                                                                                backgroundColor:
                                                                                    teamBgByDriver(
                                                                                        leaderboardData,
                                                                                        Number(
                                                                                            r.driverNumber,
                                                                                        ),
                                                                                    ) ??
                                                                                    "transparent",
                                                                            }}
                                                                        >
                                                                            <td>{r.position}</td>
                                                                            <td>
                                                                                {r.driverNumber}
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
                                                                            <td>{r.name}</td>
                                                                            <td>{r.team}</td>
                                                                            <td>
                                                                                {r.numberOfLaps}
                                                                            </td>
                                                                            <td>{r.bestLapTime}</td>
                                                                            <td>{r.lastLapTime}</td>
                                                                            <td>{r.points}</td>
                                                                            <td>{r.status}</td>
                                                                        </tr>
                                                                    ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="skeleton h-32 w-auto"></div>
                                    )}
                                </div>
                                <div className="col-span-3">
                                    {/* Starting grid */}
                                    {showStartGrid ? (
                                        <div className="card card-border bg-base-100">
                                            <div className="card-body">
                                                <h2 className="card-title">STARTING GRID</h2>
                                                <div className="mt-2">
                                                    <StartingGrid results={results} />
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="skeleton h-32 w-auto"></div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
                </>
            )}

            
        </>
    );
}

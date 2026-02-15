import StatCard from "@/components/StatCard";
import { useToast } from "@/components/ToastContext";
import type { currentSeasonData, TeamSummaryData, blockState } from "@/types";
import { color } from "framer-motion";
import { useEffect, useState, useMemo } from "react";
import DriverCard from "@/components/DriverCard";
import { VRBuilderBuildControls } from "@/components/VRBuilderBuildControls";
import { VRBuilderLivePreview } from "@/components/VRBuilderLivePreview";
import { VRBuilderInsightsReports } from "@/components/VRBuilderInsightsReports";
import type { ChartResponse } from "@/components/ChartCard";
import type { MultiSelectOption } from "@/components/MultiSelect";
import { fetchJson } from "../helpers/api";
import { BlockedCard } from "@/components/BlockedCard";

type TeamOption = { name: string; ergast_id: string };

export function TeamsPage() {
    // -- Toast
    const toast = useToast();

    const [showTeamSelection, setShowTeamSelection] = useState(true);
    const [teamOptions, setTeamOptions] = useState<TeamOption[]>([]);
    const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
    const [selectedTeamErgastID, setSelectedTeamErgastID] = useState<string | null>(null);
    const [search, setSearch] = useState("");

    const filteredTeams = useMemo(() => {
        return teamOptions.filter((team) => team.name.toLowerCase().includes(search.toLowerCase()));
    }, [teamOptions, search]);

    // -- Header
    const [showHeader, setShowHeader] = useState(false);

    // -- Tabs
    const [activeTab, setActiveTab] = useState<"summary" | "vrbuilder" | "">("");
    const [showTabs, setShowTabs] = useState(false);
    const [showVRBuilderSection, setShowVRBuilderSection] = useState(false);
    const [showSummarySection, setShowSummarySection] = useState(false);

    // -- Summary section
    const [showCurrentSeasonBox, setShowCurrentSeasonBox] = useState(false);
    const [showHero, setShowHero] = useState(false);
    const [currentSeasonData, setCurrentSeasonData] = useState<currentSeasonData | null>(null);
    const [teamSummary, setTeamSummary] = useState<TeamSummaryData | null>(null);

    const [showTeamSummary, setShowTeamSummary] = useState(false);

    const [blockCurrentSeason, setBlockCurrentSeason] = useState<blockState>({
        blocked: false,
        reason: "",
    });

    // -- VR Builder
    const [previewChart, setPreviewChart] = useState<ChartResponse | null>(null);
    const [reportBlocks, setReportBlocks] = useState<ChartResponse[]>([]);
    const [chartLoading, setChartLoading] = useState(false);

    useEffect(() => {
        fetchJson<{ teams: TeamOption[] }>("http://localhost:8000/api/teams/")
            .then((data) => setTeamOptions(data.teams))
            .catch((err) => {
                console.error("Failed to load teams", err);
                toast(err.message || "Failed to load teams.", "error");
            });
    }, []);

    // Handles tabs
    useEffect(() => {
        switch (activeTab) {
            case "summary":
                setShowSummarySection(true);
                setShowVRBuilderSection(false);
                break;
            case "vrbuilder":
                setShowSummarySection(false);
                setShowVRBuilderSection(true);
                break;

            default:
                setShowSummarySection(false);
                setShowVRBuilderSection(false);
                break;
        }
    }, [activeTab]);

    const handleSearch = () => {
        if (!selectedTeam?.toLowerCase().includes(search.toLowerCase())) {
            alert("Selected team not found.");
            return;
        }

        setShowTeamSelection(false);
        setShowTabs(true);
        setActiveTab("summary");

        setShowHero(true);
        setShowHeader(true);

        // Fetches current season data
        console.log("Fetching current season data");
        fetchJson<currentSeasonData>(
            `http://localhost:8000/api/general/${encodeURIComponent(selectedTeam)}/team/currentseason/`,
        )
            .then((json: currentSeasonData) => {
                setCurrentSeasonData(json);
                console.log("Current season JSON:", json);
            })
            .catch((err) => {
                console.error("Failed to load current season data", err);
                toast("Failed to load current season data: " + err.message, "error");
                setBlockCurrentSeason({
                    blocked: true,
                    reason: err.message,
                });
            })
            .finally(() => {
                setShowCurrentSeasonBox(true);
            });

        // Fetches summary data
        console.log("Fetching summary data");
        fetchJson<TeamSummaryData>(
            `http://localhost:8000/api/teams/${selectedTeamErgastID}/summary/`,
        )
            .then((json: TeamSummaryData) => {
                setTeamSummary(json);
                console.log("Summary JSON:", json);
            })
            .catch((err) => {
                console.error("Failed to load summary data", err);
                toast("Failed to load summary data: " + err.message, "error");
            })
            .finally(() => {
                setShowTeamSummary(true);
            });
    };

    return (
        <>
            {/* Team Selection Section */}
            {showTeamSelection && (
                <div className="h-full flex items-center justify-center">
                    <div className="flex flex-col items-center">
                        {/* Team selection */}
                        <h1 className="text-center text-5xl font-medium mb-2">Find a Team</h1>
                        <p className="text-md text-slate-500 mb-8">
                            Get information about teams in Formula 1.
                        </p>

                        <div className="card card-border bg-base-200 w-200">
                            <div className="card-body">
                                <div className="card-actions justify-center">
                                    <div className="dropdown">
                                        {/* Trigger = search input */}
                                        <div tabIndex={0} className="btn bg-base-100 p-0 w-100">
                                            <input
                                                type="text"
                                                placeholder="Search team..."
                                                value={search}
                                                onChange={(e) => setSearch(e.target.value)}
                                                className="input input-ghost w-full"
                                            />
                                        </div>

                                        {/* Dropdown */}
                                        <ul
                                            tabIndex={0}
                                            className="dropdown-content menu bg-base-100 rounded-box z-10 w-100 shadow max-h-96 overflow-y-auto"
                                        >
                                            {filteredTeams.length > 0 ? (
                                                filteredTeams.map((team) => (
                                                    <li key={team.ergast_id}>
                                                        <button
                                                            type="button"
                                                            onClick={() => {
                                                                setSelectedTeam(team.name);
                                                                setSelectedTeamErgastID(
                                                                    team.ergast_id,
                                                                );
                                                                setSearch(team.name); // show selection
                                                                console.log(team.ergast_id);
                                                            }}
                                                        >
                                                            {team.name}
                                                        </button>
                                                    </li>
                                                ))
                                            ) : (
                                                <li className="text-sm opacity-60 px-2 py-1">
                                                    No results
                                                </li>
                                            )}
                                        </ul>
                                    </div>
                                    {selectedTeam && (
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
                </div>
            )}

            {/* -- Main  section -- */}
            {/* Header */}
            {showHeader && (
                <div className="flex items-center justify-between w-full mb-2">
                    <button
                        className="btn bg-base-100 flex items-center gap-2"
                        onClick={() => {
                            window.location.href = "/teams";
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

                        <span>Find another Team</span>
                    </button>

                    <div className="text-lg font-semibold">Teams</div>
                </div>
            )}

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
                                        page={"Team"}
                                        selectedTeam={selectedTeam ?? undefined}
                                        setPreviewChart={setPreviewChart}
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

            {/* -- Summary section */}
            {showSummarySection && (
                <>
                    <div className="mt-2">
                        <div className="grid grid-cols-3 gap-2">
                            <div className="col-span-3">
                                {/* Hero */}
                                {showHero ? (
                                    <>
                                        <div
                                            className="card card-border w-auto h-80"
                                            style={{
                                                background: `
      linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)),
      #${currentSeasonData?.drivers[0].team_colour ?? "000000"}
    `,
                                            }}
                                        >
                                            <div className="card-body text-center flex flex-col justify-center items-center">
                                                <h2 className="card-title text-5xl text-white">
                                                    {selectedTeam?.toUpperCase()}
                                                </h2>
                                                <div className="text-md text-white/80">
                                                    Formula 1 Team
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="skeleton h-32 w-auto"></div>
                                )}
                            </div>
                            <div className="col-span-3">
                                {/* Team Summary */}
                                {showTeamSummary ? (
                                    <div className="card card-border bg-base-100">
                                        <div className="card-body">
                                            <h2 className="card-title">TEAM SUMMARY</h2>
                                            <div className="grid grid-cols-7 gap-4">
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            teamSummary?.grand_prix_entered ?? "N/A"
                                                        }
                                                        title="Grand Prix Entered"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={teamSummary?.team_points ?? "N/A"}
                                                        title="Team Points"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            (teamSummary?.highest_race_finish ??
                                                                "N/A") +
                                                            ` (x${teamSummary?.highest_race_finish_count ?? "N/A"})`
                                                        }
                                                        title="Highest Race Finish"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={teamSummary?.podiums ?? "N/A"}
                                                        title="Podiums"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            (teamSummary?.highest_grid_position ??
                                                                "N/A") +
                                                            ` (x${teamSummary?.highest_grid_position_count ?? "N/A"})`
                                                        }
                                                        title="Highest Grid Position"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={teamSummary?.pole_positions ?? "N/A"}
                                                        title="Pole Positions"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            teamSummary?.world_championships ??
                                                            "N/A"
                                                        }
                                                        title="World Championships"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="skeleton h-32 w-auto"></div>
                                )}
                            </div>
                            <div className="col-span-3">
                                {/* Current Season */}
                                {showCurrentSeasonBox ? (
                                    <>
                                        {blockCurrentSeason.blocked ? (
                                            <BlockedCard
                                                title="Current Season Stats Disabled"
                                                reason={blockCurrentSeason.reason}
                                            />
                                        ) : (
                                            <div className="card card-border bg-base-100 w-auto">
                                                <div className="card-body">
                                                    <h2 className="card-title mb-3">
                                                        CURRENT SEASON -{" "}
                                                        {currentSeasonData?.year ?? "N/A"}{" "}
                                                    </h2>
                                                    <div className="grid grid-cols-7 gap-4">
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.season_position ??
                                                                    "N/A"
                                                                }
                                                                title="Season Position"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.season_points ??
                                                                    "N/A"
                                                                }
                                                                title="Season Points"
                                                            />
                                                        </div>
                                                    </div>
                                                    <hr className="my-4"></hr>
                                                    <div className="grid grid-cols-7 gap-4">
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.gp.races ??
                                                                    "N/A"
                                                                }
                                                                title="Grand Prix Races"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.gp.points ??
                                                                    "N/A"
                                                                }
                                                                title="Grand Prix Points"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.gp.wins ??
                                                                    "N/A"
                                                                }
                                                                title="Grand Prix Wins"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.gp.podiums ??
                                                                    "N/A"
                                                                }
                                                                title="Grand Prix Podiums"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.gp.poles ??
                                                                    "N/A"
                                                                }
                                                                title="Grand Prix Poles"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.gp.top10s ??
                                                                    "N/A"
                                                                }
                                                                title="Grand Prix Top 10s"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.gp.dnfs ??
                                                                    "N/A"
                                                                }
                                                                title="Grand Prix DNFs"
                                                            />
                                                        </div>
                                                    </div>
                                                    <hr className="my-4"></hr>
                                                    <div className="grid grid-cols-7 gap-4">
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.sprint
                                                                        .races ?? "N/A"
                                                                }
                                                                title="Sprint Races"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.sprint
                                                                        .points ?? "N/A"
                                                                }
                                                                title="Sprint Points"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.sprint
                                                                        .wins ?? "N/A"
                                                                }
                                                                title="Sprint Wins"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.sprint
                                                                        .podiums ?? "N/A"
                                                                }
                                                                title="Sprint Podiums"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.sprint
                                                                        .poles ?? "N/A"
                                                                }
                                                                title="Sprint Poles"
                                                            />
                                                        </div>
                                                        <div className="...">
                                                            <StatCard
                                                                value={
                                                                    currentSeasonData?.sprint
                                                                        .top10s ?? "N/A"
                                                                }
                                                                title="Sprint Top 10s"
                                                            />
                                                        </div>
                                                    </div>
                                                    <hr className="my-4"></hr>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        {currentSeasonData?.drivers.map(
                                                            (driver) => (
                                                                <div className="...">
                                                                    <DriverCard
                                                                        key={driver.driver_number}
                                                                        driver={driver}
                                                                    />
                                                                </div>
                                                            ),
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="skeleton h-32 w-auto"></div>
                                )}
                            </div>
                        </div>
                    </div>
                </>
            )}
        </>
    );
}

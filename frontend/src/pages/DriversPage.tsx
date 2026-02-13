import StatCard from "@/components/StatCard";
import { useToast } from "@/components/ToastContext";
import type { currentSeasonData, DriverSummaryData } from "@/types";
import { useEffect, useState, useMemo } from "react";
import DriverCard from "@/components/DriverCard";
import { VRBuilderBuildControls } from "@/components/VRBuilderBuildControls";
import { VRBuilderLivePreview } from "@/components/VRBuilderLivePreview";
import { VRBuilderInsightsReports } from "@/components/VRBuilderInsightsReports";
import type { ChartResponse } from "@/components/ChartCard";
import TeamCard from "@/components/TeamCard";
import { fetchJson } from "@/helpers/api";

type DriverRow = {
    ergast_id: string;
    given_name: string;
    family_name: string;
};

type DriverOption = {
    id: string; // ergast_id
    name: string; // "Given Family"
};

export function DriversPage() {
    // -- Toast
    const toast = useToast();

    const [showDriverSelection, setShowDriverSelection] = useState(true);
    const [driverOptions, setDriverOptions] = useState<DriverOption[]>([]);
    const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
    const [selectedDriverErgastID, setSelectedDriverErgastID] = useState<string | null>(null);
    const [selectedDriverCode, setSelectedDriverCode] = useState<string | null>(null);
    const [search, setSearch] = useState("");

    const filteredDrivers = useMemo(() => {
        return driverOptions.filter((d) => d.name.toLowerCase().includes(search.toLowerCase()));
    }, [driverOptions, search]);

    // -- Tabs
    const [activeTab, setActiveTab] = useState<"summary" | "vrbuilder" | "">("");
    const [showTabs, setShowTabs] = useState(false);
    const [showVRBuilderSection, setShowVRBuilderSection] = useState(false);
    const [showSummarySection, setShowSummarySection] = useState(false);

    // -- Header
    const [showHeader, setShowHeader] = useState(false);

    // -- Summary section
    const [showCurrentSeasonBox, setShowCurrentSeasonBox] = useState(false);
    const [showHero, setShowHero] = useState(false);
    const [currentSeasonData, setCurrentSeasonData] = useState<currentSeasonData | null>(null);
    const [driverSummary, setDriverSummary] = useState<DriverSummaryData | null>(null);

    // -- VR Builder
    const [previewChart, setPreviewChart] = useState<ChartResponse | null>(null);
    const [reportBlocks, setReportBlocks] = useState<ChartResponse[]>([]);
    const [chartLoading, setChartLoading] = useState(false);

    useEffect(() => {
        fetchJson<{ drivers: DriverRow[] }>("http://localhost:8000/api/drivers/")
            .then((data: { drivers: DriverRow[] }) => {
                const options: DriverOption[] = data.drivers.map((d) => ({
                    id: d.ergast_id,
                    name: `${d.given_name} ${d.family_name}`,
                }));
                setDriverOptions(options);
            })
            .catch((err) => {
                console.error("Failed to load drivers", err);
                toast(err.message || "Failed to load drivers.", "error");
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
        if (!selectedDriver?.toLowerCase().includes(search.toLowerCase())) {
            alert("Selected driver not found.");
            return;
        }

        setShowDriverSelection(false);
        setShowTabs(true);
        setActiveTab("summary");

        // test
        setShowHeader(true);

        // Fetches driver code
        console.log("Fetching driver code");
        fetchJson<{ driverCode: string }>(
            `http://localhost:8000/api/drivers/${selectedDriverErgastID}/code/`,
        )
            .then((json) => {
                setSelectedDriverCode(json.driverCode);
                setShowHero(true);
                console.log("Selected driver's code:", json.driverCode);
            })
            .catch((err) => {
                console.error("Failed to load selected driver's code", err);
                toast(err.message || "Failed to load selected driver's code.", "error");
            });

        // Fetches current season data
        console.log("Fetching current season data");
        fetchJson<currentSeasonData>(
            `http://localhost:8000/api/general/${encodeURIComponent(selectedDriver)}/driver/currentseason/`,
        )
            .then((json: currentSeasonData) => {
                setCurrentSeasonData(json);
                setShowCurrentSeasonBox(true);
                console.log("Current season JSON:", json);
            })
            .catch((err) => {
                console.error("Failed to load current season data", err);
                toast(err.message || "Failed to load current season data.", "error");
            });

        // Fetches summary data
        console.log("Fetching summary data");
        fetch(`http://localhost:8000/api/drivers/${selectedDriverErgastID}/summary/`)
            .then((res) => res.json())
            .then((json: DriverSummaryData) => {
                setDriverSummary(json);
                setShowSummarySection(true);
                console.log("Summary JSON:", json);
            })
            .catch((err) => {
                console.error("Failed to load summary data", err);
                toast("Failed to load summary data: " + err.message, "error");
            });
    };

    return (
        <>
            {/* Driver Selection Section */}
            {showDriverSelection && (
                <div className="h-full flex items-center justify-center">
                    <div className="flex flex-col items-center">
                        {/* Driver selection */}
                        <h1 className="text-center text-5xl font-medium mb-2">Find a Driver</h1>
                        <p className="text-md text-slate-500 mb-8">
                            Get information about a driver in Formula 1.
                        </p>

                        <div className="card card-border bg-base-200 w-200">
                            <div className="card-body">
                                <div className="card-actions justify-center">
                                    <div className="dropdown">
                                        {/* Trigger = search input */}
                                        <div tabIndex={0} className="btn bg-base-100 p-0 w-100">
                                            <input
                                                type="text"
                                                placeholder="Search driver..."
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
                                            {filteredDrivers.length > 0 ? (
                                                filteredDrivers.map((driver) => (
                                                    <li key={driver.id}>
                                                        <button
                                                            type="button"
                                                            onClick={() => {
                                                                setSelectedDriver(driver.name);
                                                                setSelectedDriverErgastID(
                                                                    driver.id,
                                                                );
                                                                setSearch(driver.name); // show selection
                                                                console.log(driver.id);
                                                            }}
                                                        >
                                                            {driver.name}
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
                                    {selectedDriver && (
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
                            window.location.href = "/drivers";
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

                        <span>Find another Driver</span>
                    </button>

                    <div className="text-lg font-semibold">Drivers</div>
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
                                        page={"Driver"}
                                        setPreviewChart={setPreviewChart}
                                        setChartLoading={setChartLoading}
                                        chartLoading={chartLoading}
                                        selectedDriverCode={selectedDriverCode ?? undefined}
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
                                {showHero && (
                                    <>
                                        <div
                                            className="card card-border w-auto h-80"
                                            style={{
                                                background: `
      linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)),
      #${currentSeasonData?.drivers?.[0]?.team_colour ?? "000000"}
    `,
                                            }}
                                        >
                                            <div className="card-body text-center flex flex-col justify-center items-center">
                                                <h2 className="card-title text-5xl text-white">
                                                    {selectedDriver?.toUpperCase()}
                                                </h2>
                                                <div className="text-md text-white/80">
                                                    Formula 1 Driver
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>

                            <div className="col-span-3">
                                {/* Driver Summary */}
                                {showSummarySection && (
                                    <div className="card card-border bg-base-100">
                                        <div className="card-body">
                                            <h2 className="card-title">DRIVER SUMMARY</h2>
                                            <div className="grid grid-cols-7 gap-4">
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            driverSummary?.grand_prix_entered ??
                                                            "N/A"
                                                        }
                                                        title="Grand Prix Entered"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            driverSummary?.career_points ?? "N/A"
                                                        }
                                                        title="Career Points"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            (driverSummary?.highest_race_finish ??
                                                                "N/A") +
                                                            ` (x${driverSummary?.highest_race_finish_count ?? "N/A"})`
                                                        }
                                                        title="Highest Race Finish"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={driverSummary?.podiums ?? "N/A"}
                                                        title="Podiums"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            (driverSummary?.highest_grid_position ??
                                                                "N/A") +
                                                            ` (x${driverSummary?.highest_grid_position_count ?? "N/A"})`
                                                        }
                                                        title="Highest Grid Position"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            driverSummary?.pole_positions ?? "N/A"
                                                        }
                                                        title="Pole Positions"
                                                    />
                                                </div>
                                                <div className="...">
                                                    <StatCard
                                                        value={
                                                            driverSummary?.world_championships ??
                                                            "N/A"
                                                        }
                                                        title="World Championships"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="col-span-3">
                                {/* Current Season */}
                                {showCurrentSeasonBox && (
                                    <>
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
                                                                currentSeasonData?.gp?.races ??
                                                                "N/A"
                                                            }
                                                            title="Grand Prix Races"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.gp?.points ??
                                                                "N/A"
                                                            }
                                                            title="Grand Prix Points"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.gp?.wins ?? "N/A"
                                                            }
                                                            title="Grand Prix Wins"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.gp?.podiums ??
                                                                "N/A"
                                                            }
                                                            title="Grand Prix Podiums"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.gp?.poles ??
                                                                "N/A"
                                                            }
                                                            title="Grand Prix Poles"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.gp?.top10s ??
                                                                "N/A"
                                                            }
                                                            title="Grand Prix Top 10s"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.gp?.dnfs ?? "N/A"
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
                                                                currentSeasonData?.sprint?.races ??
                                                                "N/A"
                                                            }
                                                            title="Sprint Races"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.sprint?.points ??
                                                                "N/A"
                                                            }
                                                            title="Sprint Points"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.sprint?.wins ??
                                                                "N/A"
                                                            }
                                                            title="Sprint Wins"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.sprint
                                                                    ?.podiums ?? "N/A"
                                                            }
                                                            title="Sprint Podiums"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.sprint?.poles ??
                                                                "N/A"
                                                            }
                                                            title="Sprint Poles"
                                                        />
                                                    </div>
                                                    <div className="...">
                                                        <StatCard
                                                            value={
                                                                currentSeasonData?.sprint?.top10s ??
                                                                "N/A"
                                                            }
                                                            title="Sprint Top 10s"
                                                        />
                                                    </div>
                                                </div>
                                                <hr className="my-4"></hr>
                                                <div className="grid grid-cols-1 gap-4">
                                                    {currentSeasonData?.drivers?.map((driver) => (
                                                        <div className="...">
                                                            <TeamCard
                                                                key={driver.driver_number}
                                                                driver={driver}
                                                                team={driver.team_name}
                                                            />
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </>
            )}
        </>
    );
}

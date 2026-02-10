import { useEffect, useState, useMemo } from "react";

export function TeamsPage() {
    const [showTeamSelection, setShowTeamSelection] = useState(true);
    const [teamOptions, setTeamOptions] = useState<string[]>([]);
    const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
    const [search, setSearch] = useState("");

    const filteredTeams = useMemo(() => {
        return teamOptions.filter((team) => team.toLowerCase().includes(search.toLowerCase()));
    }, [teamOptions, search]);

    // -- Tabs
    const [activeTab, setActiveTab] = useState<"summary" | "vrbuilder" | "">("");
    const [showTabs, setShowTabs] = useState(false);
    const [showVRBuilderSection, setShowVRBuilderSection] = useState(false);
    const [showSummarySection, setShowSummarySection] = useState(false);

    // -- Summary section
    const [showCurrentSeasonBox, setShowCurrentSeasonBox] = useState(false);
    const [showTeamSummary, setShowTeamSummary] = useState(false);

    // Gets teams
    useEffect(() => {
        fetch("http://localhost:8000/api/teams/")
            .then((res) => res.json())
            .then((data) => setTeamOptions(data.teams.map(String)))
            .catch(console.error);
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

        // test
        setShowCurrentSeasonBox(true);
        setShowTeamSummary(true);
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
                                                    <li key={team}>
                                                        <button
                                                            type="button"
                                                            onClick={() => {
                                                                setSelectedTeam(team);
                                                                setSearch(team); // show selection
                                                            }}
                                                        >
                                                            {team}
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

            {/* -- Summary section */}
            <div className="">
                {showSummarySection && (
                    <>
                        <div className="mt-2">
                            <div className="grid grid-cols-3 gap-2">
                                <div className="col-span-3">
                                    {/* Results */}
                                    {showCurrentSeasonBox && (
                                        <>
                                            <div className="card card-border bg-base-100 w-auto">
                                                <div className="card-body">
                                                    <h2 className="card-title">
                                                        {selectedTeam?.toUpperCase()} - TEAM
                                                    </h2>
                                                    <p>Current Season</p>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>
                                <div className="col-span-3">
                                    {/* Starting grid */}
                                    {showTeamSummary && (
                                        <div className="card card-border bg-base-100">
                                            <div className="card-body">
                                                <h2 className="card-title">TEAM SUMMARY</h2>
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

import { ChevronDownIcon } from "@heroicons/react/20/solid";
import { useState, useEffect, useRef } from "react";
import { DriverAvatar } from "../components/DriverAvatar";
import { StartingGrid } from "../components/StartingGrid";
import { RacePlayback } from "../components/RacePlayback";
import { RacePlaybackLeaderboard } from "../components/RacePlaybackLeaderboard";
import { WeatherInfo } from "../components/RacePlaybackWeatherInfo";
import { PlaybackControls } from "../components/PlaybackControls";
import type { PlaybackData } from "../types";

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
  const [yearOptions, setYearOptions] = useState<string[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [countryOptions, setCountryOptions] = useState<string[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [sessionsOptions, setSessionsOptions] = useState<string[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>("");
  const [circuitName, setCircuitName] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [searchButton, setSearchButton] = useState(false);
  const [loadingResults, setLoadingResults] = useState(false);
  const [showResultsBox, setShowResultsBox] = useState(false);
  const [activeTab, setActiveTab] = useState<"summary" | "playback" | "">("");
  const [showTabs, setShowTabs] = useState(false);
  const [showStartGrid, setShowStartGrid] = useState(false);
  const raceSessionsWithGridPos = [
    "Race",
    "Sprint",
    "Sprint Shootout",
    "Sprint Qualifying",
  ];
  const [showSummarySection, setShowSummarySection] = useState(false);
  const [showRacePlayBackSection, setShowRacePlayBackSection] = useState(false);

  // -- Race Playback
  const [currentTime, setCurrentTime] = useState(0);
  const [showRacePlayBackBox, setShowRacePlayBackBox] = useState(false);
  const [showRacePlayBackHeader, setShowRacePlayBackHeader] = useState(false);
  const [showRacePlayBackWeatherInfo, setShowRacePlayBackWeatherInfo] =
    useState(false);
  const [showRacePlayBackLeaderboard, setShowRacePlayBackLeaderboard] =
    useState(false);

  const [data, setData] = useState<PlaybackData | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);

  const frameRef = useRef<number | null>(null);
  const lastTimestampRef = useRef<number | null>(null);

  // Helper function for getting playback data for race viewer
  // Fetch playback data
  useEffect(() => {
    const url = `http://localhost:8000/api/session/${selectedYear}/${encodeURIComponent(
      selectedCountry
    )}/${encodeURIComponent(selectedSession)}/playback/`;

    fetch(url)
      .then((res) => res.json())
      .then((json: PlaybackData) => {
        setData(json);
        setCurrentTime(0);
        setIsPlaying(false);
      })
      .catch((err) => console.error("Failed to load playback", err));
  }, [selectedYear, selectedCountry, selectedSession]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !data) {
      // if paused, make sure nothing keeps running
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
      lastTimestampRef.current = null;
      return;
    }

    const tick = (timestamp: number) => {
      if (lastTimestampRef.current == null) {
        lastTimestampRef.current = timestamp;
      }

      const deltaSec =
        ((timestamp - lastTimestampRef.current) / 1000) * speedMultiplier;
      lastTimestampRef.current = timestamp;

      setCurrentTime((prev) => {
        const next = Math.min(prev + deltaSec, data.raceDuration);
        if (next >= data.raceDuration) {
          // stop at end
          setIsPlaying(false);
        }
        return next;
      });

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
  }, [isPlaying, speedMultiplier, data]);
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
        break;

      case "playback":
        setShowSummarySection(false);
        setShowRacePlayBackSection(true);
        break;

      default:
        setShowSummarySection(false);
        setShowRacePlayBackSection(false);
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

    if (raceSessionsWithGridPos.includes(selectedSession)) {
      console.log("showing start grid");
      setShowStartGrid(true);
    }

    fetch(
      `http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/result/`
    )
      .then((res) => res.json())
      .then((data: { results: Result[] }) => {
        setResults(data.results);
      })
      .catch((err) => {
        console.error("Failed to load results", err);
      })
      .finally(() => {
        setLoadingResults(false);
      });
  };

  // Whenever race selection is touched, hide everything to restart
  useEffect(() => {
    setShowTabs(false);
    setShowSummarySection(false);
    setShowRacePlayBackSection(false);
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
                    className="btn flex items-center gap-2"
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
                          onClick={() => setSelectedCountry(country)}
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
                    className="btn flex items-center gap-2"
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
                          onClick={() => setSelectedSession(session)}
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
                  className="btn ms-5"
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

      {/* -- Main session section -- */}
      {/* Tabs */}
      {showTabs && (
        <div role="tablist" className="tabs tabs-box mt-4">
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
        </div>
      )}

      {/* -- Race Playback section */}
      <div className="mt-4">
        {showRacePlayBackSection && (
          <>
            {/* Header */}

            {/* Race playback circuit */}
            <PlaybackControls
              data={data}
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              speedMultiplier={speedMultiplier}
              setSpeedMultiplier={setSpeedMultiplier}
            />

            {/* Race playback weather info */}
            <WeatherInfo
              year={parseInt(selectedYear)}
              country={selectedCountry}
              session={selectedSession}
              currentTime={currentTime}
            />

            {/* Race playback leaderboard */}
            <RacePlaybackLeaderboard
              year={parseInt(selectedYear)}
              country={selectedCountry}
              session={selectedSession}
              currentTime={currentTime}
            />

            {/* Race playback circuit */}
            <RacePlayback data={data} currentTime={currentTime} />
          </>
        )}
      </div>

      {/* -- Summary section */}
      <div className="mt-4">
        {showSummarySection && (
          <>
            {/* Results */}
            {showResultsBox && (
              <>
                <div className="card card-border bg-base-100 w-auto mt-5">
                  <div className="card-body">
                    <h2 className="card-title">
                      {circuitName.toUpperCase()} {selectedYear} GRAND PRIX -{" "}
                      {selectedSession.toUpperCase()}
                    </h2>
                    <p>
                      Results of the selected session.
                      <br />
                      <em>
                        Note: Certain sessions, particularly older sessions, may
                        not have lap data available.
                      </em>
                    </p>

                    <div className="overflow-x-auto">
                      <table className="table mt-5">
                        {!loadingResults && (
                          <thead>
                            <>
                              {selectedSession.includes("Practice") && (
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

                              {(selectedSession.includes("Qualifying") ||
                                selectedSession.includes("Shootout")) && (
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

                              {(selectedSession.includes("Race") ||
                                selectedSession.includes("Sprint")) && (
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
                        )}
                        <tbody>
                          {loadingResults ? (
                            <tr>
                              <td colSpan={7} className="p-0">
                                <div className="skeleton h-32 w-auto"></div>
                              </td>
                            </tr>
                          ) : (
                            <>
                              {selectedSession.includes("Practice") &&
                                sortedResults.map((r) => (
                                  <tr
                                    key={`${r.driverNumber}-${r.position}`}
                                    style={{
                                      backgroundColor:
                                        "#" + r.team_color + "33",
                                    }}
                                  >
                                    <td>{r.position}</td>
                                    <td>{r.driverNumber}</td>
                                    <td>
                                      <div className="flex items-center gap-3">
                                        <DriverAvatar
                                          name={r.name}
                                          headshotUrl={r.headshot_url}
                                        />
                                      </div>
                                    </td>
                                    <td>{r.name}</td>
                                    <td>{r.team}</td>
                                    <td>{r.bestLapTime}</td>
                                    <td>{r.numberOfLaps}</td>
                                  </tr>
                                ))}

                              {(selectedSession.includes("Qualifying") ||
                                selectedSession.includes("Shootout")) &&
                                sortedResults.map((r) => (
                                  <tr key={`${r.driverNumber}-${r.position}`}>
                                    <td>{r.position}</td>
                                    <td>{r.driverNumber}</td>
                                    <td>
                                      <div className="flex items-center gap-3">
                                        <DriverAvatar
                                          name={r.name}
                                          headshotUrl={r.headshot_url}
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

                              {(selectedSession.includes("Race") ||
                                selectedSession.includes("Sprint")) &&
                                sortedResults.map((r) => (
                                  <tr key={`${r.driverNumber}-${r.position}`}>
                                    <td>{r.position}</td>
                                    <td>{r.driverNumber}</td>
                                    <td>
                                      <div className="flex items-center gap-3">
                                        <DriverAvatar
                                          name={r.name}
                                          headshotUrl={r.headshot_url}
                                        />
                                      </div>
                                    </td>
                                    <td>{r.name}</td>
                                    <td>{r.team}</td>
                                    <td>{r.numberOfLaps}</td>
                                    <td>{r.bestLapTime}</td>
                                    <td>{r.lastLapTime}</td>
                                    <td>{r.points}</td>
                                    <td>{r.status}</td>
                                  </tr>
                                ))}
                            </>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </>
            )}
            {/* Starting grid */}
            {showStartGrid && (
              <div className="card card-border bg-base-100 mt-5 ">
                <div className="card-body">
                  <h2 className="card-title">STARTING GRID</h2>
                  <div className="mt-2">
                    {loadingResults ? (
                      <div className="skeleton h-32 w-auto"></div>
                    ) : (
                      <StartingGrid results={results} />
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

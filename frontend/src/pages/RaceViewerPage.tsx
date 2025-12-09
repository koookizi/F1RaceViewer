import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/20/solid'
import { useState, useEffect } from "react";

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
  status: string;
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

  // Gets results
  useEffect(() => {
  fetch(`http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/${selectedSession}/result/`)
    .then((res) => res.json())
    .then((data: { results: Result[] }) => {
      console.log("API data:", data);          // 👈 add this

      setResults(data.results);
    })
    .catch((err) => console.error("Failed to load results", err));
  }, [selectedSession]);   

  // Gets years
  useEffect(() => {
  fetch("http://localhost:8000/api/seasons_years/")
    .then(res => res.json())
    .then(data => setYearOptions(data.years.map(String)))
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
    });
  }, [selectedYear]); // Basically means, if selectedYear changes, then this block executes.

  // Gets sessions
    useEffect(() => {
  if (!selectedCountry) {
    setSessionsOptions([]);
    setSelectedSession("");
    return;
  }
  fetch(`http://localhost:8000/api/seasons/${selectedYear}/${selectedCountry}/sessions/`)
    .then((res) => res.json())
    .then((data: { sessions: string[] }) => {
      setSessionsOptions(data.sessions);
    })
    .catch((err) => {
      console.error("Failed to load sessions", err);
    });
  }, [selectedCountry]);

  // Get circuit
  useEffect(() => {
  fetch(`http://localhost:8000/api/session/${selectedYear}/${selectedCountry}/circuit/`)
    .then((res) => res.json())
    .then((data) => {
      setCircuitName(data.circuit);
    })
    .catch((err) => console.error("Error fetching circuit:", err));
  }, [selectedSession]);

  const sortedResults = [...results].sort((a, b) => a.position - b.position);


  return (
    <>
      <h1 className="text-5xl font-bold tracking-tight text-slate-100">
        Race Viewer
      </h1>


      <div className="card card-border bg-base-100 w-auto mt-10">
        <div className="card-body">
          <h2 className="card-title">Race Selection</h2>
          <div className="card-actions justify-start">
            
            {/* Year dropdown */}
            <div className="dropdown">
              <div
                tabIndex={0}
                role="button"
                className="btn flex items-center gap-2"
              >
                {selectedYear || "Select Year"}
                {/* Optional: your Chevron icon */}
                <ChevronDownIcon aria-hidden="true" className="size-5 opacity-70" />
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
                {/* Optional: your Chevron icon */}
                <ChevronDownIcon aria-hidden="true" className="size-5 opacity-70" />
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
                  {/* Optional: your Chevron icon */}
                  <ChevronDownIcon aria-hidden="true" className="size-5 opacity-70" />
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
          </div>
        </div>
      </div>

      {selectedSession && (
        <div className="card card-border bg-base-100 w-auto mt-5">
        <div className="card-body">
          <h2 className="card-title">{circuitName.toUpperCase()} {selectedYear} GRAND PRIX</h2>
          <p>A card component has a figure, a body part, and inside body there are title and actions parts</p>
            <tbody>
              {sortedResults.map((r) => (
                <tr key={`${r.driverNumber}-${r.position}`}>
                  <td>{r.position}</td>
                  <td>{r.abbreviation}</td>
                  <td>{r.name}</td>
                  <td>{r.team}</td>
                  <td>{r.q1 ?? "-"}</td>
                  <td>{r.q2 ?? "-"}</td>
                  <td>{r.q3 ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </div>
        </div>

      )}

    </>
  );
}

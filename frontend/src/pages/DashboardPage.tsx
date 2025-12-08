import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/20/solid'
import { useState, useEffect } from "react";


export function DashboardPage() {
  const [yearOptions, setYearOptions] = useState<string[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>("");    
  const [countryOptions, setCountryOptions] = useState<string[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [sessionsOptions, setSessionsOptions] = useState<string[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>("");

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
  fetch(`http://localhost:8000/api/seasons/${selectedYear}/${selectedCountry}/sessions`)
    .then((res) => res.json())
    .then((data: { sessions: string[] }) => {
      setSessionsOptions(data.sessions);
    })
    .catch((err) => {
      console.error("Failed to load sessions", err);
    });
  }, [selectedCountry]);


  return (
    <>
      <h1 className="text-5xl font-bold tracking-tight text-slate-100">
        Race Viewer
      </h1>
      <p className="mt-4 text-lg text-slate-300 pb-5">
        Your F1 data will appear here.
      </p>

      {/* Year dropdown */}
      <Menu as="div" className="relative inline-block">
      <MenuButton className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white/10 px-3 py-2 text-sm font-semibold text-white ring-1 ring-inset ring-white/5 hover:bg-white/20">
        {selectedYear || "Select Year"}
        <ChevronDownIcon aria-hidden="true" className="-mr-1 size-5 text-gray-400" />
      </MenuButton>

      <MenuItems
        transition
        className="absolute left-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-gray-800 outline outline-1 -outline-offset-1 outline-white/10 transition data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[leave]:duration-75 data-[enter]:ease-out data-[leave]:ease-in max-h-96 overflow-y-auto"
      >
        {yearOptions.map((label) => (
          <MenuItem key={label}>
            {({ active }) => (
              <button
                onClick={() => setSelectedYear(label)}
                className={`block w-full px-4 py-2 text-left text-sm ${
                  active ? "bg-white/5 text-white" : "text-gray-300"
                }`}
              >
                {label}
              </button>
            )}
          </MenuItem>
        ))}
      </MenuItems>
    </Menu>

    {/* Country dropdown */}
    <Menu as="div" className="relative inline-block">
      <MenuButton className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white/10 px-3 py-2 text-sm font-semibold text-white ring-1 ring-inset ring-white/5 hover:bg-white/20">
        {selectedCountry || "Select Country"}
        <ChevronDownIcon aria-hidden="true" className="-mr-1 size-5 text-gray-400" />
      </MenuButton>

      <MenuItems
        transition
        className="absolute left-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-gray-800 outline outline-1 -outline-offset-1 outline-white/10 transition data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[leave]:duration-75 data-[enter]:ease-out data-[leave]:ease-in max-h-96 overflow-y-auto"
      >
        {countryOptions.map((label) => (
          <MenuItem key={label}>
            {({ active }) => (
              <button
                onClick={() => setSelectedCountry(label)}
                className={`block w-full px-4 py-2 text-left text-sm ${
                  active ? "bg-white/5 text-white" : "text-gray-300"
                }`}
              >
                {label}
              </button>
            )}
          </MenuItem>
        ))}
      </MenuItems>
    </Menu>

    {/* Sessions dropdown */}
    <Menu as="div" className="relative inline-block">
      <MenuButton className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white/10 px-3 py-2 text-sm font-semibold text-white ring-1 ring-inset ring-white/5 hover:bg-white/20">
        {selectedSession || "Select Session"}
        <ChevronDownIcon aria-hidden="true" className="-mr-1 size-5 text-gray-400" />
      </MenuButton>

      <MenuItems
        transition
        className="absolute left-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-gray-800 outline outline-1 -outline-offset-1 outline-white/10 transition data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[leave]:duration-75 data-[enter]:ease-out data-[leave]:ease-in max-h-96 overflow-y-auto"
      >
        {sessionsOptions.map((label) => (
          <MenuItem key={label}>
            {({ active }) => (
              <button
                onClick={() => setSelectedSession(label)}
                className={`block w-full px-4 py-2 text-left text-sm ${
                  active ? "bg-white/5 text-white" : "text-gray-300"
                }`}
              >
                {label}
              </button>
            )}
          </MenuItem>
        ))}
      </MenuItems>
    </Menu>

    </>
  );
}

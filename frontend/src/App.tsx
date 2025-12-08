import React, { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { DashboardPage } from "./pages/DashboardPage";
import { TrackMapPage } from "./pages/TrackMapPage";
import { StandingsPage } from "./pages/StandingsPage";
import { WeatherPage } from "./pages/WeatherPage";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      {/* Mobile top bar */}
      <header className="fixed inset-x-0 top-0 z-20 flex items-center gap-3 border-b border-slate-800 bg-slate-900/90 px-4 py-3 md:hidden">
        <button
          className="flex flex-col gap-[3px]"
          onClick={() => setSidebarOpen(true)}
        >
          <span className="h-[2px] w-5 rounded-full bg-slate-100" />
          <span className="h-[2px] w-5 rounded-full bg-slate-100" />
          <span className="h-[2px] w-5 rounded-full bg-slate-100" />
        </button>
        <span className="text-sm font-semibold tracking-tight">
          F1 Race Viewer
        </span>
      </header>

      {/* Layout: sidebar + main content */}
      <div className="flex min-h-screen pt-12 md:pt-0">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <main className="flex-1 px-6 py-8 md:px-12">
          <Routes>
            {/* redirect / to /dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/track-map" element={<TrackMapPage />} />
            <Route path="/standings" element={<StandingsPage />} />
            <Route path="/weather" element={<WeatherPage />} />

            {/* optional 404 */}
            <Route
              path="*"
              element={<p className="text-slate-300">Page not found.</p>}
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;

import React, { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { RaceViewerPage } from "./pages/RaceViewerPage";
import { CircuitsPage } from "./pages/CircuitsPage";
import { DriversPage } from "./pages/DriversPage";

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
            <Route path="/" element={<Navigate to="/race-viewer" replace />} />

            <Route path="/race-viewer" element={<RaceViewerPage />} />
            <Route path="/circuits" element={<CircuitsPage />} />
            <Route path="/drivers" element={<DriversPage />} />

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

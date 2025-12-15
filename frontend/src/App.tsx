import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { RaceViewerPage } from "./pages/RaceViewerPage";
import { CircuitsPage } from "./pages/CircuitsPage";
import { DriversPage } from "./pages/DriversPage";

function App() {
  return (
    <Routes>
      <Route element={<Sidebar />}>
        {/* redirect / → /race-viewer */}
        <Route path="/" element={<Navigate to="/race-viewer" replace />} />

        <Route path="/race-viewer" element={<RaceViewerPage />} />
        <Route path="/circuits" element={<CircuitsPage />} />
        <Route path="/drivers" element={<DriversPage />} />

        <Route
          path="*"
          element={<p className="text-slate-300">Page not found.</p>}
        />
      </Route>
    </Routes>
  );
}

export default App;

import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { RaceViewerPage } from "./pages/RaceViewerPage";
import { TeamsPage } from "./pages/TeamsPage";
import { DriversPage } from "./pages/DriversPage";
import { ToastProvider } from "./components/ToastContext";

function App() {
    return (
        <ToastProvider>
            <Routes>
                <Route element={<Sidebar />}>
                    {/* redirect / → /race-viewer */}
                    <Route path="/" element={<Navigate to="/race-viewer" replace />} />

                    <Route path="/race-viewer" element={<RaceViewerPage />} />
                    <Route path="/teams" element={<TeamsPage />} />
                    <Route path="/drivers" element={<DriversPage />} />

                    <Route path="*" element={<p className="text-slate-300">Page not found.</p>} />
                </Route>
            </Routes>
        </ToastProvider>
    );
}

export default App;

import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { HomePage } from "./pages/HomePage";
import { RaceViewerPage } from "./pages/RaceViewerPage";
import { TeamsPage } from "./pages/TeamsPage";
import { DriversPage } from "./pages/DriversPage";
import { ToastProvider } from "./components/ToastContext";

function HomeLayout() {
    return <Outlet />;
}

function SidebarLayout() {
    return <Sidebar />;
}

function App() {
    return (
        <ToastProvider>
            <Routes>
                <Route element={<HomeLayout />}>
                    <Route index element={<HomePage />} />
                </Route>

                <Route element={<SidebarLayout />}>
                    <Route path="race-viewer" element={<RaceViewerPage />} />
                    <Route path="teams" element={<TeamsPage />} />
                    <Route path="drivers" element={<DriversPage />} />
                </Route>

                <Route path="dashboard" element={<Navigate to="/race-viewer" replace />} />
                <Route path="*" element={<p className="text-slate-300">Page not found.</p>} />
            </Routes>
        </ToastProvider>
    );
}

export default App;
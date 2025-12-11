import { NavLink } from "react-router-dom";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const navItems = [
  { to: "/race-viewer", label: "Race Viewer" },
  { to: "/drivers", label: "Drivers" },
  { to: "/circuits", label: "Circuits" },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile backdrop */}
      <div
        className={`
          fixed inset-0 z-30 bg-black/50 transition-opacity md:hidden
          ${open ? "opacity-100" : "pointer-events-none opacity-0"}
        `}
        onClick={onClose}
      />

      {/* Sidebar panel */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-40 w-56
          border-r border-slate-800
          bg-gradient-to-b from-slate-900 to-slate-950
          px-4 py-4
          transition-transform
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:static md:translate-x-0
        `}
      >
        <div className="flex h-full flex-col">
          <div className="mb-6 text-xs font-bold uppercase tracking-[0.25em] text-slate-400">
            F1 Race Viewer
          </div>

          <nav className="space-y-2 text-sm">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }: { isActive: boolean }) =>
                  [
                    "flex w-full items-center rounded-lg px-3 py-2 text-left transition",
                    isActive
                      ? "bg-slate-800 text-slate-100"
                      : "text-slate-300 hover:bg-slate-800/70 hover:text-slate-100",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </aside>
    </>
  );
}

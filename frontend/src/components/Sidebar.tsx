import { Outlet, NavLink } from "react-router-dom";

export function Sidebar() {
  return (
    <div className="drawer lg:drawer-open">
      <input id="my-drawer-4" type="checkbox" className="drawer-toggle" />
      <div className="drawer-content">
        {/* Navbar */}
        <nav className="navbar w-full bg-base-300">
          <label
            htmlFor="my-drawer-4"
            aria-label="open sidebar"
            className="btn btn-square btn-ghost"
          >
            {/* Sidebar toggle icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              strokeLinejoin="round"
              strokeLinecap="round"
              strokeWidth="2"
              fill="none"
              stroke="currentColor"
              className="my-1.5 inline-block size-4"
            >
              <path d="M4 4m0 2a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2z"></path>
              <path d="M9 4v16"></path>
              <path d="M14 10l2 2l-2 2"></path>
            </svg>
          </label>
          <div className="px-4">Navbar Title</div>
        </nav>
        {/* Page content here */}
        <main className="flex-1 max-w-full overflow-x-hidden px-6 py-8 md:px-12">
          <Outlet />
        </main>
      </div>

      <div className="drawer-side is-drawer-close:overflow-visible">
        <label
          htmlFor="my-drawer-4"
          aria-label="close sidebar"
          className="drawer-overlay"
        ></label>
        <div className="flex min-h-full flex-col items-start bg-base-200 is-drawer-close:w-14 is-drawer-open:w-64">
          {/* Sidebar content here */}
          <ul className="menu w-full grow">
            {/* List item */}
            <li>
              <NavLink
                to="/race-viewer"
                className={({ isActive }) =>
                  `
                flex items-center gap-3
                is-drawer-close:tooltip is-drawer-close:tooltip-right
                ${isActive ? "active font-semibold" : ""}
                `
                }
                data-tip="Race Viewer"
              >
                <i className="bi bi-search"></i>

                <span className="is-drawer-close:hidden">Race Viewer</span>
              </NavLink>
            </li>

            <li>
              <NavLink
                to="/circuits"
                className={({ isActive }) =>
                  `
                flex items-center gap-3
                is-drawer-close:tooltip is-drawer-close:tooltip-right
                ${isActive ? "active font-semibold" : ""}
                `
                }
                data-tip="Circuits"
              >
                <i className="bi bi-pin-map-fill"></i>

                <span className="is-drawer-close:hidden">Circuits</span>
              </NavLink>
            </li>

            <li>
              <NavLink
                to="/drivers"
                className={({ isActive }) =>
                  `
                flex items-center gap-3
                is-drawer-close:tooltip is-drawer-close:tooltip-right
                ${isActive ? "active font-semibold" : ""}
                `
                }
                data-tip="Drivers"
              >
                <i className="bi bi-person-fill"></i>

                <span className="is-drawer-close:hidden">Drivers</span>
              </NavLink>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

import { NavLink, Outlet } from "react-router";
import { LevelSwitcher } from "../components/LevelSwitcher";
import { StatusBar } from "../components/StatusBar";

const NAV: readonly { readonly to: string; readonly label: string }[] = [
  { to: "/", label: "Start here" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/labs", label: "Hands-on labs" },
  { to: "/architecture", label: "Architecture" },
  { to: "/evidence", label: "Evidence" },
];

const TOOLS: readonly { readonly to: string; readonly label: string }[] = [
  { to: "/learn", label: "Learn the concepts" },
  { to: "/patterns", label: "Pattern library" },
  { to: "/data", label: "Data" },
  { to: "/agent", label: "Agent sandbox" },
  { to: "/bakeoff", label: "Bake-off" },
  { to: "/demo", label: "Offline verification" },
];

export function Layout() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to main content
      </a>
      <header className="app-header">
        <div className="app-header__inner">
          <div className="app-header__top">
            <NavLink
              to="/"
              end
              className="brand"
              aria-label="Fabric Foundry Integration Accelerator, home"
            >
              <span className="brand__mark" aria-hidden="true">
                FF
              </span>
              <span className="brand__text">
                <span className="brand__name">Fabric Foundry Integration Accelerator</span>
                <span className="brand__tagline">
                  Understand the roles. Build a workflow. Verify the result.
                </span>
              </span>
            </NavLink>
            <LevelSwitcher />
          </div>
          <nav aria-label="Primary" className="app-nav">
            <ul>
              {NAV.map((item) => (
                <li key={item.to}>
                  <NavLink to={item.to} end={item.to === "/"}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
              <li className="explore-menu">
                <details>
                  <summary>Explore</summary>
                  <nav aria-label="Explore tools">
                    {TOOLS.map((item) => (
                      <NavLink key={item.to} to={item.to}>
                        {item.label}
                      </NavLink>
                    ))}
                  </nav>
                </details>
              </li>
            </ul>
          </nav>
        </div>
      </header>
      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>
      <StatusBar />
    </>
  );
}

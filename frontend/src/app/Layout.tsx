import { NavLink, Outlet } from "react-router";
import { LevelSwitcher } from "../components/LevelSwitcher";
import { StatusBar } from "../components/StatusBar";

const NAV: readonly { readonly to: string; readonly label: string }[] = [
  { to: "/", label: "Workshop" },
  { to: "/learn", label: "Learn" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/patterns", label: "Patterns" },
  { to: "/evidence", label: "Evidence" },
];

const TOOLS: readonly { readonly to: string; readonly label: string }[] = [
  { to: "/architecture", label: "Architecture" },
  { to: "/labs", label: "Hands-on labs" },
  { to: "/data", label: "Data" },
  { to: "/agent", label: "Agent sandbox" },
  { to: "/bakeoff", label: "Bake-off" },
  { to: "/demo", label: "Demo" },
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
                <span className="brand__tagline">Reference architecture · Patterns · Workshop</span>
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
            </ul>
          </nav>
        </div>
      </header>
      <nav aria-label="Workshop tools" className="workshop-tools">
        {TOOLS.map((item) => (
          <NavLink key={item.to} to={item.to}>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>
      <StatusBar />
    </>
  );
}

import { NavLink, Outlet } from "react-router";
import { LevelSwitcher } from "../components/LevelSwitcher";
import { StatusBar } from "../components/StatusBar";

const NAV: readonly { readonly to: string; readonly label: string }[] = [
  { to: "/", label: "Home" },
  { to: "/architecture", label: "Architecture" },
  { to: "/patterns", label: "Patterns" },
  { to: "/learn", label: "Learn" },
  { to: "/labs", label: "Labs" },
  { to: "/guides", label: "Guides" },
  { to: "/data", label: "Data" },
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
      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>
      <StatusBar />
    </>
  );
}

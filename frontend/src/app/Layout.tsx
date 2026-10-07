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
        <div className="app-header__title">
          <p className="app-header__eyebrow">Reference architecture · Pattern catalog · Workshop</p>
          <p className="app-header__name">Fabric Foundry Integration Accelerator</p>
        </div>
        <LevelSwitcher />
        <nav aria-label="Primary">
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
      </header>
      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>
      <StatusBar />
    </>
  );
}

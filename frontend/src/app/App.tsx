import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";
import { HomePage } from "../features/home/HomePage";
import { Layout } from "./Layout";
import { NotFoundPage } from "./NotFoundPage";

// Feature pages load on demand so the first paint stays small.
const ArchitecturePage = lazy(() =>
  import("../features/architecture/ArchitecturePage").then((m) => ({
    default: m.ArchitecturePage,
  })),
);
const PatternsPage = lazy(() =>
  import("../features/patterns/PatternsPage").then((m) => ({ default: m.PatternsPage })),
);
const PatternDetailPage = lazy(() =>
  import("../features/patterns/PatternDetailPage").then((m) => ({ default: m.PatternDetailPage })),
);
const LearnPage = lazy(() =>
  import("../features/learn/LearnPage").then((m) => ({ default: m.LearnPage })),
);
const LessonPage = lazy(() =>
  import("../features/learn/LessonPage").then((m) => ({ default: m.LessonPage })),
);
const LabsPage = lazy(() =>
  import("../features/labs/LabsPage").then((m) => ({ default: m.LabsPage })),
);
const LabPage = lazy(() =>
  import("../features/labs/LabPage").then((m) => ({ default: m.LabPage })),
);
const GuidesPage = lazy(() =>
  import("../features/guides/GuidesPage").then((m) => ({ default: m.GuidesPage })),
);
const GuideRunnerPage = lazy(() =>
  import("../features/guides/GuideRunnerPage").then((m) => ({ default: m.GuideRunnerPage })),
);
const DataPage = lazy(() =>
  import("../features/data/DataPage").then((m) => ({ default: m.DataPage })),
);
const AgentPage = lazy(() =>
  import("../features/agents/AgentPage").then((m) => ({ default: m.AgentPage })),
);
const BakeoffPage = lazy(() =>
  import("../features/bakeoff/BakeoffPage").then((m) => ({ default: m.BakeoffPage })),
);
const BakeoffRunPage = lazy(() =>
  import("../features/bakeoff/BakeoffPage").then((m) => ({ default: m.BakeoffRunPage })),
);
const DemoPage = lazy(() =>
  import("../features/demo/DemoPage").then((m) => ({ default: m.DemoPage })),
);
const EvidencePage = lazy(() =>
  import("../features/workshop/EvidencePage").then((m) => ({ default: m.EvidencePage })),
);

function LegacyGuideRedirect() {
  const location = useLocation();
  return (
    <Navigate
      replace
      to={`${location.pathname.replace(/^\/guides(?=\/|$)/, "/use-cases")}${location.search}${location.hash}`}
    />
  );
}

function Page({ children }: { readonly children: ReactNode }) {
  return (
    <Suspense
      fallback={
        <p className="loading" role="status">
          Loading page…
        </p>
      }
    >
      {children}
    </Suspense>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route
          path="architecture/:viewId"
          element={
            <Page>
              <ArchitecturePage />
            </Page>
          }
        />
        <Route
          path="architecture"
          element={
            <Page>
              <ArchitecturePage />
            </Page>
          }
        />
        <Route
          path="patterns"
          element={
            <Page>
              <PatternsPage />
            </Page>
          }
        />
        <Route
          path="patterns/:patternId"
          element={
            <Page>
              <PatternDetailPage />
            </Page>
          }
        />
        <Route
          path="learn"
          element={
            <Page>
              <LearnPage />
            </Page>
          }
        />
        <Route
          path="learn/:lessonId"
          element={
            <Page>
              <LessonPage />
            </Page>
          }
        />
        <Route
          path="labs"
          element={
            <Page>
              <LabsPage />
            </Page>
          }
        />
        <Route
          path="labs/:labId"
          element={
            <Page>
              <LabPage />
            </Page>
          }
        />
        <Route
          path="use-cases"
          element={
            <Page>
              <GuidesPage />
            </Page>
          }
        />
        <Route
          path="use-cases/:guideId"
          element={
            <Page>
              <GuideRunnerPage />
            </Page>
          }
        />
        <Route
          path="use-cases/:guideId/:stepId"
          element={
            <Page>
              <GuideRunnerPage />
            </Page>
          }
        />
        <Route path="guides/*" element={<LegacyGuideRedirect />} />
        <Route
          path="evidence"
          element={
            <Page>
              <EvidencePage />
            </Page>
          }
        />
        <Route
          path="data"
          element={
            <Page>
              <DataPage />
            </Page>
          }
        />
        <Route
          path="agent"
          element={
            <Page>
              <AgentPage />
            </Page>
          }
        />
        <Route
          path="bakeoff"
          element={
            <Page>
              <BakeoffPage />
            </Page>
          }
        />
        <Route
          path="bakeoff/runs/:runId"
          element={
            <Page>
              <BakeoffRunPage />
            </Page>
          }
        />
        <Route
          path="demo"
          element={
            <Page>
              <DemoPage />
            </Page>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

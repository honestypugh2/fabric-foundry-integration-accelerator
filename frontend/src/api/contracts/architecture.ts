import { z } from "zod";
import { capabilityStatus, operatingMode } from "./common";

const levelTextSchema = z.object({
  executive: z.string(),
  l100: z.string(),
  l200: z.string(),
  l300: z.string(),
  l400: z.string(),
});
export const architectureSchema = z.object({
  layers: z.array(
    z.object({ id: z.string(), name: z.string(), question: z.string(), summary: z.string() }),
  ),
  components: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      layer: z.string(),
      status: capabilityStatus,
      description: levelTextSchema,
      owns: z.array(z.string()),
      does_not_own: z.array(z.string()),
      pattern_ids: z.array(z.string()),
      offline_equivalent: z.string(),
      sources: z.array(z.string()),
    }),
  ),
  flows: z.array(
    z.object({
      id: z.string(),
      source: z.string(),
      target: z.string(),
      label: z.string(),
      kind: z.enum([
        "context",
        "reasoning",
        "access",
        "authority",
        "evidence",
        "fallback",
        "change",
      ]),
    }),
  ),
});
export type ArchitectureMap = z.output<typeof architectureSchema>;
export type ArchitectureComponent = ArchitectureMap["components"][number];

export const completenessSchema = z.object({
  total: z.number(),
  answered: z.number(),
  coverage: z.number(),
  items: z.array(
    z.object({
      id: z.string(),
      question: z.string(),
      answered: z.boolean(),
      answered_by: z.array(z.string()),
      planned_phase: z.number().nullable(),
    }),
  ),
});
export type Completeness = z.output<typeof completenessSchema>;

const nodeKind = z.enum([
  "person",
  "client",
  "harness",
  "knowledge",
  "app",
  "service",
  "foundry",
  "fabric",
  "data",
  "mcp",
  "gateway",
  "identity",
  "policy",
  "evidence",
  "local",
  "external",
]);
const nodeState = z.enum([
  "implemented",
  "planned",
  "documented",
  "preview",
  "tenant-validation",
  "optional",
]);
const runtimeBinding = z.enum([
  "agents",
  "api",
  "mcp",
  "fabric-local",
  "fabric-live",
  "foundry",
  "changes",
  "audit",
  "education",
  "evaluation",
  "router",
]);
const edgeKind = z.enum([
  "context",
  "reasoning",
  "access",
  "authority",
  "evidence",
  "fallback",
  "change",
  "data",
  "config",
]);
const boxSchema = z.object({ x: z.number(), y: z.number(), w: z.number(), h: z.number() });
const pointSchema = z.tuple([z.number(), z.number()]);

export const viewSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  kind: z.string(),
  summary: z.string(),
  doc: z.string().nullable(),
  pattern_ids: z.array(z.string()),
});
export type ViewSummary = z.output<typeof viewSummarySchema>;

export const diagramViewSchema = z.object({
  id: z.string(),
  title: z.string(),
  kind: z.enum(["reference", "system", "topology", "flow", "maturity", "resilience"]),
  summary: z.string(),
  cue: z.string(),
  aligned_to: z.array(z.string()),
  pattern_ids: z.array(z.string()),
  doc: z.string().nullable(),
  steps: z.array(z.object({ id: z.string(), label: z.string(), cue: z.string() })),
  zones: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      kind: z.enum(["local", "tenant", "fabric", "foundry", "github", "optional", "offline"]),
      step: z.string().nullable(),
    }),
  ),
  nodes: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      sublabel: z.string(),
      kind: nodeKind,
      state: nodeState,
      step: z.string().nullable(),
      component: z.string().nullable(),
      summary: z.string(),
      repo_path: z.string().nullable(),
      phase: z.number().nullable(),
      runtime: runtimeBinding.nullable(),
      sources: z.array(z.string()),
    }),
  ),
  edges: z.array(
    z.object({
      id: z.string(),
      source: z.string(),
      target: z.string(),
      label: z.string(),
      kind: edgeKind,
      step: z.string().nullable(),
      planned: z.boolean(),
    }),
  ),
  bands: z.array(
    z.object({
      id: z.string(),
      kind: z.enum(["identity", "policy", "evidence", "failure", "network"]),
      text: z.string(),
      step: z.string().nullable(),
    }),
  ),
  traces: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      summary: z.string(),
      label: z.enum(["PLANNED FLOW", "LOCAL", "SIMULATED", "PREVIEW", "DOCUMENTED"]),
      demo_act: z.number().nullable(),
      steps: z.array(
        z.object({
          node: z.string(),
          edge: z.string().nullable(),
          say: z.string(),
          note: z.string(),
        }),
      ),
    }),
  ),
});
export type DiagramView = z.output<typeof diagramViewSchema>;
export type DiagramNode = DiagramView["nodes"][number];
export type DiagramTrace = DiagramView["traces"][number];

export const viewLayoutSchema = z.object({
  width: z.number(),
  height: z.number(),
  grid_bottom: z.number(),
  nodes: z.record(z.string(), boxSchema),
  zones: z.record(z.string(), boxSchema),
  edges: z.record(
    z.string(),
    z.object({ points: z.array(pointSchema), label_at: pointSchema, label_fraction: z.number() }),
  ),
});
export type ViewLayout = z.output<typeof viewLayoutSchema>;

export const renderedViewSchema = z.object({ view: diagramViewSchema, layout: viewLayoutSchema });
export type RenderedView = z.output<typeof renderedViewSchema>;

export const viewRuntimeSchema = z.object({
  view_id: z.string(),
  operating_mode: operatingMode,
  observed_at: z.string(),
  nodes: z.array(
    z.object({
      node: z.string(),
      binding: runtimeBinding,
      status: z.enum(["ACTIVE", "READY", "DEGRADED", "UNAVAILABLE", "NOT CONFIGURED"]),
      label: z.string(),
      detail: z.string(),
    }),
  ),
});
export type ViewRuntime = z.output<typeof viewRuntimeSchema>;
export type NodeRuntime = ViewRuntime["nodes"][number];

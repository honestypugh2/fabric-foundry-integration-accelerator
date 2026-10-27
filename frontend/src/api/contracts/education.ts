import { z } from "zod";
import { level, capabilityStatus, executionLabel, evidenceCategory } from "./common";

export const lessonSummarySchema = z.object({
  id: z.string(),
  area: z.string(),
  title: z.string(),
  summary: z.string(),
  status: capabilityStatus,
  pattern_ids: z.array(z.string()),
  related_labs: z.array(z.string()),
  related_guides: z.array(z.string()),
});
export type LessonSummary = z.output<typeof lessonSummarySchema>;

const researchLensSchema = z.object({
  question: z.string(),
  foundations: z.array(
    z.object({ idea: z.string(), explanation: z.string(), application: z.string() }),
  ),
  evolution: z.array(z.string()),
  hypothesis: z.string(),
  experiment: z.string(),
  baseline: z.string(),
  metrics: z.array(z.string()),
  limitations: z.array(z.string()),
  sources: z.array(z.string()),
});
const learningBriefSchema = z.object({
  lesson_id: z.string(),
  what: z.string(),
  why: z.string(),
  when: z.string(),
  when_not: z.string(),
  how: z.array(z.string()),
  expected_result: z.string(),
  failure_and_recovery: z.string(),
  diagram: z.string().nullable(),
  research: researchLensSchema,
});
export type LearningBrief = z.output<typeof learningBriefSchema>;

export const workshopSchema = z.object({
  label: z.literal("LOCAL"),
  content: z.object({
    version: z.literal(1),
    title: z.string(),
    summary: z.string(),
    execution_summary: z.string(),
    execution_paths: z.array(
      z.object({
        mode: z.enum(["OFFLINE", "HYBRID", "LIVE"]),
        title: z.string(),
        description: z.string(),
        results: z.string(),
        fallback: z.string(),
        prerequisites: z.array(z.string()),
        commands: z.array(z.string()),
        safety: z.string(),
      }),
    ),
    journeys: z.array(
      z.object({
        id: z.string(),
        title: z.string(),
        summary: z.string(),
        duration_minutes: z.number(),
        lesson_ids: z.array(z.string()),
      }),
    ),
    briefs: z.array(learningBriefSchema),
    use_cases: z.array(
      z.object({
        guide_id: z.string(),
        problem: z.string(),
        audience: z.string(),
        outcomes: z.array(z.string()),
        lesson_ids: z.array(z.string()),
        stages: z.array(
          z.object({
            title: z.string(),
            task: z.string(),
            capability: z.string(),
            control: z.string(),
            evidence: z.string(),
          }),
        ),
        questions: z.array(z.string()),
        production_gaps: z.array(z.string()),
        presenter_path: z.string(),
      }),
    ),
    evidence: z.array(
      z.object({
        id: z.string(),
        category: z.enum(["DEPLOYMENT", "OPERATION", "INTERFACE"]),
        title: z.string(),
        recorded_on: z.string(),
        label: executionLabel,
        provider: z.string(),
        server: z.string(),
        tool: z.string(),
        scope: z.string(),
        limitations: z.array(z.string()),
        pattern_ids: z.array(z.string()),
        screenshot: z.string().nullable(),
        verification_record: z.string().nullable(),
      }),
    ),
  }),
  sources: z.array(
    z.object({ id: z.string(), title: z.string(), url: z.string(), publisher: z.string() }),
  ),
  coverage: z.array(
    z.object({
      pattern_id: z.string(),
      name: z.string(),
      lesson_ids: z.array(z.string()),
      lab_ids: z.array(z.string()),
      guide_ids: z.array(z.string()),
      diagram_ids: z.array(z.string()),
      evidence_ids: z.array(z.string()),
      default_demo_path: z.string(),
    }),
  ),
});
export type Workshop = z.output<typeof workshopSchema>;
export type UseCaseStory = Workshop["content"]["use_cases"][number];

export const lessonSchema = lessonSummarySchema.extend({
  teaching: learningBriefSchema.nullable(),
  learning_objectives: z.array(z.string()),
  prerequisites: z.array(z.string()),
  concepts: z.array(z.object({ term: z.string(), definition: z.string() })),
  evidence: z.array(
    z.object({ statement: z.string(), category: evidenceCategory, sources: z.array(z.string()) }),
  ),
  try_it: z.array(
    z.object({
      label: z.string(),
      command: z.string(),
      result_label: z.enum(["LOCAL", "SIMULATED", "HYBRID", "PREVIEW", "UNAVAILABLE"]),
    }),
  ),
  copilot_prompt: z.string(),
  claude_code_prompt: z.string(),
  production_notes: z.array(z.string()),
  sources: z.array(z.string()),
  levels: z.array(z.object({ level, label: z.string(), markdown: z.string() })),
  checks: z.array(
    z.object({ id: z.string(), level, question: z.string(), choices: z.array(z.string()) }),
  ),
});
export type Lesson = z.output<typeof lessonSchema>;
export type KnowledgeCheck = Lesson["checks"][number];

export const checkGradeSchema = z.object({
  check_id: z.string(),
  correct: z.boolean(),
  correct_choice: z.number(),
  explanation: z.string(),
});
export type CheckGrade = z.output<typeof checkGradeSchema>;

export const labSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string(),
  level,
  duration_minutes: z.number(),
  mode: z.enum(["OFFLINE", "HYBRID", "LIVE"]),
  pattern_ids: z.array(z.string()),
  lessons: z.array(z.string()),
});
export type LabSummary = z.output<typeof labSummarySchema>;

export const labSchema = labSummarySchema.extend({
  prerequisites: z.array(z.string()),
  steps: z.array(
    z.object({
      stage: z.string(),
      title: z.string(),
      instructions: z.string(),
      commands: z.array(z.string()),
      expected: z.string().nullable(),
      evidence_category: evidenceCategory.nullable(),
    }),
  ),
});
export type Lab = z.output<typeof labSchema>;

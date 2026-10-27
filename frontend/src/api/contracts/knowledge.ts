import { z } from "zod";

export const knowledgeResultSchema = z.object({
  knowledge_base: z.string(),
  question: z.string(),
  preview_flag: z.string(),
  enabled: z.boolean(),
  passages: z.array(
    z.object({
      text: z.string(),
      score: z.number(),
      citation: z.object({
        document: z.string(),
        title: z.string(),
        section: z.string(),
        path: z.string(),
      }),
    }),
  ),
  note: z.string(),
});
export type KnowledgeResult = z.output<typeof knowledgeResultSchema>;

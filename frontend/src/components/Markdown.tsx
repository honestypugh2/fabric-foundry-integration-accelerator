import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

/** Renders lesson Markdown through the sanitizer. Raw HTML is never rendered. */
export function Markdown({ children }: { readonly children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]} skipHtml>
        {children}
      </ReactMarkdown>
    </div>
  );
}

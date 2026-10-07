import { CopyButton } from "./CopyButton";

/** A copyable prompt or command. */
export function PromptBlock({ title, text }: { readonly title: string; readonly text: string }) {
  return (
    <figure className="prompt">
      <figcaption>
        <span>{title}</span>
        <CopyButton text={text} label={title.toLowerCase()} />
      </figcaption>
      <pre>
        <code>{text}</code>
      </pre>
    </figure>
  );
}

import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  readonly children: ReactNode;
}

interface State {
  readonly failed: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  override state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  override componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Learning workspace rendering failed.", error, info.componentStack);
  }

  override render() {
    if (this.state.failed) {
      return (
        <section role="alert" aria-labelledby="workspace-error-heading">
          <h1 id="workspace-error-heading">This page could not be displayed</h1>
          <p>
            A page failed to load or render. Reload to try again, or return to Start here. No cloud
            operation is confirmed by this message.
          </p>
          <button
            type="button"
            onClick={() => {
              window.location.reload();
            }}
          >
            Reload page
          </button>{" "}
          <a href="/">Return to Start here</a>
        </section>
      );
    }
    return this.props.children;
  }
}

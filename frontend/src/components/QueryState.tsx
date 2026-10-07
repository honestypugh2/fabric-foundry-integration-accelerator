import type { ReactNode } from "react";
import { ControlPlaneUnreachableError, describeError } from "../api/client";

interface QueryStateProps<T> {
  readonly label: string;
  readonly isPending: boolean;
  readonly error: unknown;
  readonly data: T | undefined;
  readonly children: (data: T) => ReactNode;
}

/** Explicit loading, offline and error states for every data view. */
export function QueryState<T>({ label, isPending, error, data, children }: QueryStateProps<T>) {
  if (error !== null && error !== undefined) {
    const offline = error instanceof ControlPlaneUnreachableError;
    return (
      <div className={offline ? "notice notice--offline" : "notice notice--error"} role="alert">
        <p>
          <strong>{offline ? "Control plane not reachable" : `Could not load ${label}`}</strong>
        </p>
        <p>{describeError(error)}</p>
        {offline ? (
          <p>
            Nothing is shown as live. Start the API with <code>make run-api</code>, then reload.
          </p>
        ) : null}
      </div>
    );
  }
  if (isPending || data === undefined) {
    return (
      <p className="loading" role="status">
        Loading {label}…
      </p>
    );
  }
  return <>{children(data)}</>;
}

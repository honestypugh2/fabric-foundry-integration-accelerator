import { Link } from "react-router";
import { usePageTitle } from "./usePageTitle";

export function NotFoundPage() {
  usePageTitle("Not found");
  return (
    <section aria-labelledby="not-found-heading">
      <h1 id="not-found-heading">Page not found</h1>
      <p>
        <Link to="/">Return to the home page</Link>
      </p>
    </section>
  );
}

import { Link } from "react-router";
import { useWorkshop } from "../../api/hooks";
import { QueryState } from "../../components/QueryState";

export function PatternCoverage() {
  const workshop = useWorkshop();
  return (
    <section aria-labelledby="coverage-heading">
      <h2 id="coverage-heading">Pattern coverage and readiness</h2>
      <p>
        Coverage is computed from the validated registry, not a claim that every pattern is runnable
        or live-certified. Linked lessons have five depths; a missing lab or dated evidence remains
        visible.
      </p>
      <QueryState label="pattern coverage" {...workshop}>
        {(data) => (
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Pattern coverage matrix"
          >
            <table>
              <caption>
                Concept, five-level teaching, lab, use case, architecture and evidence coverage
              </caption>
              <thead>
                <tr>
                  <th scope="col">Pattern</th>
                  <th scope="col">Five-level lessons</th>
                  <th scope="col">Offline labs</th>
                  <th scope="col">Use cases</th>
                  <th scope="col">Diagrams</th>
                  <th scope="col">Recorded evidence</th>
                  <th scope="col">Demo path</th>
                </tr>
              </thead>
              <tbody>
                {data.coverage.map((item) => (
                  <tr key={item.pattern_id}>
                    <th scope="row">
                      <Link to={`/patterns/${item.pattern_id}`}>
                        {item.pattern_id} {item.name}
                      </Link>
                    </th>
                    <td>
                      {item.lesson_ids.length
                        ? item.lesson_ids.map((id) => (
                            <Link className="coverage-link" key={id} to={`/learn/${id}`}>
                              {id}
                            </Link>
                          ))
                        : "Not authored"}
                    </td>
                    <td>
                      {item.lab_ids.length
                        ? item.lab_ids.map((id) => (
                            <Link className="coverage-link" key={id} to={`/labs/${id}`}>
                              {id}
                            </Link>
                          ))
                        : "No linked lab"}
                    </td>
                    <td>
                      {item.guide_ids.length
                        ? item.guide_ids.map((id) => (
                            <Link className="coverage-link" key={id} to={`/use-cases/${id}`}>
                              {id}
                            </Link>
                          ))
                        : "No linked use case"}
                    </td>
                    <td>
                      {item.diagram_ids.length
                        ? item.diagram_ids.map((id) => (
                            <Link className="coverage-link" key={id} to={`/architecture/${id}`}>
                              {id}
                            </Link>
                          ))
                        : "No linked diagram"}
                    </td>
                    <td>
                      {item.evidence_ids.length
                        ? item.evidence_ids.map((id) => (
                            <Link className="coverage-link" key={id} to={`/evidence#${id}`}>
                              {id}
                            </Link>
                          ))
                        : "Not recorded"}
                    </td>
                    <td>{item.default_demo_path}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </QueryState>
    </section>
  );
}

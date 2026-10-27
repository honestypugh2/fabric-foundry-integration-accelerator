# Power BI build area

Use this folder for reviewed, customer-neutral PBIP/TMDL model and report assets.
The HC-01 live model and report are not complete yet. This folder is not evidence of publication.

Start with the [HC-01 guide](../guides/hc-01-fabric-mcp-powerbi-medallion-lab/README.md) and
the [synthetic semantic contract](../data/synthetic/semantic/hc-lab-7file-v1/semantic-model.yaml).
Keep real model/workspace bindings in ignored local files.

## Deferred report review

Report rendering and screenshot review are deferred by user decision. The LOCAL
two-page draft passed schema and saved-geometry checks, but service preview could
not start its required browser. Do not install Chromium to unblock this work.
No screenshots or publication have been verified. Publication remains dependent on
rendered review, model acceptance, and separate approval.

See the [delivery backlog and ordered next steps](../docs/operations/delivery-backlog.md).
This deferral is not a report-completion or publication claim.

## Population slicer contract

Both synthetic profiles use `KEEPFILTERS` in High Risk Patient Count and the five
condition-prevalence numerators. A selection on risk category or a condition flag must
intersect the measure's classification predicate, not be replaced by it. High Risk Patient %
inherits the corrected count; its denominator remains Patient Count in the same selection.
Date and facility filters still do not back-filter the patient snapshot.

Keep `DIVIDE` and the existing DAX BLANK behavior: an excluded classification has no qualifying
patients, and an empty population does not produce a fabricated zero-percent rate. Unfiltered
baselines are unchanged. All measures remain synthetic demonstrations, not clinical metrics.

**DOCUMENTED BEHAVIOR:** Microsoft Learn's `KEEPFILTERS` reference explains intersection
versus replacement (source registry ID `dax-keepfilters` in
[sources.yaml](../docs/research/sources.yaml)).
**LOCAL:** offline tests lock the reference DAX expressions for both profiles and evaluate
the SQL baselines; they do not execute DAX.
**REQUIRES TENANT VALIDATION:** test the proposed DAX with query-scoped measures, then separately
approve any persisted LIVE update. Check conflicting selections, matching selections,
ordinary patient-attribute filters, empty populations and all 23 baseline measures.
Neither a local contract change nor a query-scoped definition updates a deployed model.
When testing a query-scoped override, also define the dependent High Risk Patient % measure
explicitly in that query; validating only the replacement count does not validate the
persisted percentage measure's dependency. Its canonical expression itself is unchanged.

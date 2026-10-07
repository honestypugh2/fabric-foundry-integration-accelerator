-- Physical role-playing date dimension for the claim date. A separate physical table per role
-- keeps every relationship active (no USERELATIONSHIP needed) in Direct Lake models.
SELECT
    "date" AS claim_date,
    "year" AS claim_year,
    "quarter" AS claim_quarter,
    "month" AS claim_month,
    month_name AS claim_month_name,
    year_month AS claim_year_month,
    day_of_week AS claim_day_of_week,
    is_weekend AS claim_is_weekend
FROM _date_spine

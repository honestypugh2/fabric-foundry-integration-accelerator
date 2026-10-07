-- Physical role-playing date dimension for the admission date. A separate physical table per role
-- keeps every relationship active (no USERELATIONSHIP needed) in Direct Lake models.
SELECT
    "date" AS admission_date,
    "year" AS admission_year,
    "quarter" AS admission_quarter,
    "month" AS admission_month,
    month_name AS admission_month_name,
    year_month AS admission_year_month,
    day_of_week AS admission_day_of_week,
    is_weekend AS admission_is_weekend
FROM _date_spine

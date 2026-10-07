-- Physical role-playing date dimension for the discharge date. A separate physical table per role
-- keeps every relationship active (no USERELATIONSHIP needed) in Direct Lake models.
SELECT
    "date" AS discharge_date,
    "year" AS discharge_year,
    "quarter" AS discharge_quarter,
    "month" AS discharge_month,
    month_name AS discharge_month_name,
    year_month AS discharge_year_month,
    day_of_week AS discharge_day_of_week,
    is_weekend AS discharge_is_weekend
FROM _date_spine

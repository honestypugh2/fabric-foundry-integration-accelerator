-- One row per calendar date covering every encounter, discharge and claim date.
WITH bounds AS (
    SELECT
        least(
            (SELECT min(encounter_date) FROM silver_encounters),
            (SELECT min(claim_date) FROM silver_claims)
        ) AS first_date,
        greatest(
            (SELECT max(discharge_date) FROM silver_encounters),
            (SELECT max(claim_date) FROM silver_claims)
        ) AS last_date
),
spine AS (
    SELECT
        CAST(
            unnest(
                generate_series(
                    CAST(first_date AS TIMESTAMP), CAST(last_date AS TIMESTAMP), INTERVAL 1 DAY
                )
            ) AS DATE
        ) AS calendar_date
    FROM bounds
)
SELECT
    calendar_date AS "date",
    year(calendar_date) AS "year",
    quarter(calendar_date) AS "quarter",
    month(calendar_date) AS "month",
    monthname(calendar_date) AS month_name,
    strftime(calendar_date, '%Y-%m') AS year_month,
    isodow(calendar_date) AS day_of_week,
    dayname(calendar_date) AS day_name,
    isodow(calendar_date) IN (6, 7) AS is_weekend
FROM spine
ORDER BY calendar_date

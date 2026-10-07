-- One row per patient and calendar year with at least one ED visit. The frequent-use threshold
-- (4 or more ED visits in a year) is a synthetic analytical definition.
SELECT
    patient_id,
    encounter_year AS "year",
    count(*) AS ed_visit_count,
    count(*) >= 4 AS is_frequent_ed_user
FROM silver_encounters
WHERE is_ed
GROUP BY patient_id, encounter_year

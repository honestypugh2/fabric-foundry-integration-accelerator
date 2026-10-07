-- One row per primary diagnosis and facility. Keeps count and total LOS so averages can be
-- re-aggregated correctly (never average grouped averages).
SELECT
    primary_diagnosis_code,
    any_value(primary_diagnosis_description) AS primary_diagnosis_description,
    facility_id,
    count(*) AS inpatient_count,
    sum(length_of_stay_days) AS total_los_days,
    round(sum(length_of_stay_days) / count(*), 2) AS average_los_days
FROM silver_encounters
WHERE is_inpatient
GROUP BY primary_diagnosis_code, facility_id

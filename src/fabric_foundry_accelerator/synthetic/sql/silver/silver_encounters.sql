-- Typed encounters with calendar fields, LOS bands and data-quality flags.
-- Uses the actual discharge_date; never approximates discharge as encounter_date + LOS.
WITH typed AS (
    SELECT
        encounter_id,
        patient_id,
        CAST(try_strptime(encounter_date, '%Y-%m-%d') AS DATE) AS encounter_date,
        encounter_time,
        CAST(try_strptime(discharge_date, '%Y-%m-%d') AS DATE) AS discharge_date,
        encounter_type,
        facility_id,
        facility_name,
        department,
        primary_diagnosis_code,
        primary_diagnosis_description,
        attending_provider,
        discharge_disposition,
        TRY_CAST(length_of_stay_days AS INTEGER) AS length_of_stay_days,
        TRY_CAST(total_charges AS DECIMAL(12, 2)) AS total_charges
    FROM bronze_encounters
)
SELECT
    *,
    year(encounter_date) AS encounter_year,
    quarter(encounter_date) AS encounter_quarter,
    month(encounter_date) AS encounter_month,
    CASE
        WHEN length_of_stay_days IS NULL THEN NULL
        WHEN length_of_stay_days = 0 THEN '0 days'
        WHEN length_of_stay_days <= 2 THEN '1-2 days'
        WHEN length_of_stay_days <= 5 THEN '3-5 days'
        ELSE '6+ days'
    END AS los_band,
    encounter_type = 'Inpatient' AS is_inpatient,
    encounter_type = 'ED' AS is_ed,
    discharge_date >= encounter_date AS is_chronology_valid,
    length_of_stay_days = date_diff('day', encounter_date, discharge_date) AS is_los_consistent,
    coalesce(
        encounter_date < max(discharge_date) OVER (
            PARTITION BY patient_id
            ORDER BY encounter_date, encounter_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ),
        false
    ) AS overlaps_prior_encounter
FROM typed

-- One row per encounter. Child tables are aggregated BEFORE joining so encounters and charges
-- are never multiplied by child rows.
WITH vitals AS (
    SELECT encounter_id, count(*) AS vital_sign_count
    FROM silver_vitals
    GROUP BY encounter_id
),
medications AS (
    SELECT encounter_id, count(*) AS medication_order_count
    FROM silver_medications
    GROUP BY encounter_id
)
SELECT
    e.encounter_id,
    e.patient_id,
    e.facility_id,
    e.encounter_date,
    e.discharge_date,
    e.encounter_year,
    e.encounter_month,
    e.encounter_type,
    e.department,
    e.primary_diagnosis_code,
    e.primary_diagnosis_description,
    e.discharge_disposition,
    e.length_of_stay_days,
    e.los_band,
    e.total_charges,
    e.is_inpatient,
    e.is_ed,
    coalesce(v.vital_sign_count, 0) AS vital_sign_count,
    coalesce(m.medication_order_count, 0) AS medication_order_count
FROM silver_encounters AS e
LEFT JOIN vitals AS v USING (encounter_id)
LEFT JOIN medications AS m USING (encounter_id)

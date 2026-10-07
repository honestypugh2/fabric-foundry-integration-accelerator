-- Medication orders at order grain with a chronology check (end_date before start_date).
WITH typed AS (
    SELECT
        medication_id,
        patient_id,
        encounter_id,
        medication_name,
        medication_class,
        dosage,
        frequency,
        prescriber,
        CAST(try_strptime(start_date, '%Y-%m-%d') AS DATE) AS start_date,
        CAST(try_strptime(end_date, '%Y-%m-%d') AS DATE) AS end_date,
        status
    FROM bronze_medications
)
SELECT
    *,
    end_date IS NULL OR end_date >= start_date AS is_chronology_valid
FROM typed

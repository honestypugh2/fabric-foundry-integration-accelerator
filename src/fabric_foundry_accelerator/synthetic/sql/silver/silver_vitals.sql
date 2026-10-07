-- Numeric vital-sign observations with a range check. The flag reports parsing/range issues only;
-- it never labels a clinical condition.
WITH typed AS (
    SELECT
        vital_id,
        patient_id,
        encounter_id,
        facility_name,
        department,
        try_strptime("timestamp", '%Y-%m-%d %H:%M:%S') AS vital_timestamp,
        TRY_CAST(heart_rate AS INTEGER) AS heart_rate,
        TRY_CAST(systolic_bp AS INTEGER) AS systolic_bp,
        TRY_CAST(diastolic_bp AS INTEGER) AS diastolic_bp,
        TRY_CAST(temperature_f AS DECIMAL(4, 1)) AS temperature_f,
        TRY_CAST(respiratory_rate AS INTEGER) AS respiratory_rate,
        TRY_CAST(spo2_percent AS INTEGER) AS spo2_percent,
        TRY_CAST(pain_level AS INTEGER) AS pain_level
    FROM bronze_vitals
)
SELECT
    *,
    NOT (
        coalesce(heart_rate BETWEEN 20 AND 250, true)
        AND coalesce(systolic_bp BETWEEN 50 AND 260, true)
        AND coalesce(diastolic_bp BETWEEN 20 AND 160, true)
        AND coalesce(temperature_f BETWEEN 90 AND 110, true)
        AND coalesce(respiratory_rate BETWEEN 4 AND 60, true)
        AND coalesce(spo2_percent BETWEEN 50 AND 100, true)
        AND coalesce(pain_level BETWEEN 0 AND 10, true)
    ) AS is_out_of_range
FROM typed

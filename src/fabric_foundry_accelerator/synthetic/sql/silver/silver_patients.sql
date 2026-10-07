-- Typed, conformed patients. Age bands and risk categories are synthetic analytical definitions.
WITH typed AS (
    SELECT
        patient_id,
        first_name,
        last_name,
        CAST(try_strptime(date_of_birth, '%Y-%m-%d') AS DATE) AS date_of_birth,
        TRY_CAST(age AS INTEGER) AS age,
        gender,
        race,
        zip_code,
        city,
        state,
        insurance_type,
        primary_care_provider,
        TRY_CAST(risk_score AS DECIMAL(4, 2)) AS risk_score
    FROM bronze_patients
)
SELECT
    *,
    CASE
        WHEN age IS NULL THEN NULL
        WHEN age < 18 THEN '0-17'
        WHEN age < 40 THEN '18-39'
        WHEN age < 65 THEN '40-64'
        ELSE '65+'
    END AS age_band,
    CASE
        WHEN risk_score IS NULL THEN NULL
        WHEN risk_score >= 0.70 THEN 'High'
        WHEN risk_score >= 0.40 THEN 'Moderate'
        ELSE 'Low'
    END AS risk_category
FROM typed

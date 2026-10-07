-- Patient-level problem list. encounter_id is blank in the source and is retained as NULL;
-- condition records are never linked to encounters artificially.
SELECT
    condition_id,
    patient_id,
    encounter_id,
    condition_code,
    condition_description,
    condition_type,
    CAST(try_strptime(date_diagnosed, '%Y-%m-%d') AS DATE) AS date_diagnosed,
    status,
    condition_type = 'Chronic' AS is_chronic,
    CASE
        WHEN starts_with(condition_code, 'E11') THEN 'Diabetes'
        WHEN starts_with(condition_code, 'I10') THEN 'Hypertension'
        WHEN starts_with(condition_code, 'I50') THEN 'Heart Failure'
        WHEN starts_with(condition_code, 'J44') THEN 'COPD'
        WHEN starts_with(condition_code, 'N18') THEN 'Chronic Kidney Disease'
        WHEN starts_with(condition_code, 'E78') THEN 'Hyperlipidemia'
        WHEN starts_with(condition_code, 'J45') THEN 'Asthma'
        WHEN starts_with(condition_code, 'E66') THEN 'Obesity'
        WHEN starts_with(condition_code, 'M17') THEN 'Osteoarthritis'
        ELSE 'Unmapped'
    END AS condition_category
FROM bronze_conditions

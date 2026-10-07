-- One row per patient, INCLUDING patients with zero conditions. Condition flags count Active
-- conditions in each reviewed category. Multimorbidity groups and risk categories are synthetic
-- analytical definitions.
WITH conditions AS (
    SELECT
        patient_id,
        count(*) AS condition_count,
        count(DISTINCT CASE
            WHEN is_chronic AND status = 'Active' AND condition_category <> 'Unmapped'
                THEN condition_category
        END) AS chronic_condition_count,
        bool_or(condition_category = 'Diabetes' AND status = 'Active') AS has_diabetes,
        bool_or(condition_category = 'Hypertension' AND status = 'Active') AS has_hypertension,
        bool_or(condition_category = 'Heart Failure' AND status = 'Active') AS has_heart_failure,
        bool_or(condition_category = 'COPD' AND status = 'Active') AS has_copd,
        bool_or(condition_category = 'Chronic Kidney Disease' AND status = 'Active') AS has_ckd
    FROM silver_conditions
    GROUP BY patient_id
)
SELECT
    p.patient_id,
    p.age_band,
    p.risk_category,
    coalesce(c.condition_count, 0) AS condition_count,
    coalesce(c.chronic_condition_count, 0) AS chronic_condition_count,
    CASE
        WHEN coalesce(c.chronic_condition_count, 0) = 0 THEN 'No active chronic conditions'
        WHEN c.chronic_condition_count = 1 THEN '1 chronic condition'
        WHEN c.chronic_condition_count <= 3 THEN '2-3 chronic conditions'
        ELSE '4+ chronic conditions'
    END AS multimorbidity_group,
    coalesce(c.has_diabetes, false) AS has_diabetes,
    coalesce(c.has_hypertension, false) AS has_hypertension,
    coalesce(c.has_heart_failure, false) AS has_heart_failure,
    coalesce(c.has_copd, false) AS has_copd,
    coalesce(c.has_ckd, false) AS has_ckd
FROM silver_patients AS p
LEFT JOIN conditions AS c USING (patient_id)

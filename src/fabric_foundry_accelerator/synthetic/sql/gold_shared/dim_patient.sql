-- Patient dimension for analytics. Direct identifiers (names, date of birth) are intentionally
-- excluded: Gold carries only what reporting needs.
SELECT
    p.patient_id,
    p.age,
    p.age_band,
    p.gender,
    p.race,
    p.city,
    p.state,
    p.insurance_type,
    p.risk_score,
    p.risk_category,
    ph.condition_count,
    ph.chronic_condition_count,
    ph.multimorbidity_group,
    ph.has_diabetes,
    ph.has_hypertension,
    ph.has_heart_failure,
    ph.has_copd,
    ph.has_ckd
FROM silver_patients AS p
INNER JOIN gold_population_health AS ph USING (patient_id)

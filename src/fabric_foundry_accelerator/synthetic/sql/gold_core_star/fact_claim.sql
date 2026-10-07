-- One row per claim, keyed to the payer master.
SELECT
    c.claim_id,
    c.encounter_id,
    c.patient_id,
    e.facility_id,
    d.payer_key,
    c.claim_date,
    c.claim_amount,
    c.paid_amount,
    c.denied_amount,
    c.patient_responsibility,
    c.claim_status,
    c.is_denied,
    c.denial_reason,
    c.days_to_payment,
    c.payment_ratio
FROM silver_claims AS c
LEFT JOIN silver_encounters AS e ON e.encounter_id = c.encounter_id
LEFT JOIN dim_payer AS d ON d.payer_name = c.payer

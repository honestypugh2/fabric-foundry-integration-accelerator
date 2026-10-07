-- Claims with decimal money. is_denied means claim_status = 'Denied' only;
-- 'Paid on Appeal' stays a separate status. payment_ratio is guarded against zero claim_amount.
WITH typed AS (
    SELECT
        claim_id,
        patient_id,
        encounter_id,
        CAST(try_strptime(claim_date, '%Y-%m-%d') AS DATE) AS claim_date,
        payer,
        payer_type,
        TRY_CAST(claim_amount AS DECIMAL(12, 2)) AS claim_amount,
        TRY_CAST(paid_amount AS DECIMAL(12, 2)) AS paid_amount,
        TRY_CAST(denied_amount AS DECIMAL(12, 2)) AS denied_amount,
        TRY_CAST(patient_responsibility AS DECIMAL(12, 2)) AS patient_responsibility,
        denial_reason,
        claim_status,
        TRY_CAST(days_to_payment AS INTEGER) AS days_to_payment
    FROM bronze_claims
)
SELECT
    *,
    claim_status = 'Denied' AS is_denied,
    CASE WHEN claim_amount > 0 THEN round(paid_amount / claim_amount, 4) END AS payment_ratio
FROM typed

-- Payer dimension with a surrogate payer_key (this profile has no payer master).
SELECT
    'PYR-' || lpad(CAST(row_number() OVER (ORDER BY payer, payer_type) AS VARCHAR), 2, '0') AS payer_key,
    payer,
    payer_type
FROM (SELECT DISTINCT payer, payer_type FROM silver_claims)

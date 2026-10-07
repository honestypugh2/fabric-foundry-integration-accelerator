-- Payer dimension from the payer master.
SELECT payer_id AS payer_key, payer_name, payer_type
FROM silver_payers

-- One row per index inpatient encounter. SYNTHETIC DEMONSTRATION RULE, not a validated clinical
-- readmission specification:
--   * next qualifying admission = the next inpatient admission strictly after the index
--     discharge_date (no unrestricted self-join over every encounter pair);
--   * readmitted when that interval is 1 through 30 days inclusive;
--   * follow-up eligible when at least 30 days of observation remain before the cutoff
--     (the latest encounter_date in the dataset). Ineligible rows are kept and flagged so
--     measures can exclude them from BOTH numerator and denominator.
WITH inpatient AS (
    SELECT encounter_id, patient_id, facility_id, encounter_date AS admission_date, discharge_date
    FROM silver_encounters
    WHERE is_inpatient AND is_chronology_valid
),
cutoff AS (
    SELECT max(encounter_date) AS observation_cutoff FROM silver_encounters
),
with_next AS (
    SELECT
        i.*,
        (
            SELECT min(n.admission_date)
            FROM inpatient AS n
            WHERE n.patient_id = i.patient_id AND n.admission_date > i.discharge_date
        ) AS next_admission_date
    FROM inpatient AS i
)
SELECT
    w.encounter_id AS index_encounter_id,
    w.patient_id,
    w.facility_id,
    w.admission_date AS index_admission_date,
    w.discharge_date AS index_discharge_date,
    w.next_admission_date,
    date_diff('day', w.discharge_date, w.next_admission_date) AS days_to_next_admission,
    coalesce(date_diff('day', w.discharge_date, w.next_admission_date) BETWEEN 1 AND 30, false)
        AS is_readmitted_30d,
    w.discharge_date + 30 <= c.observation_cutoff AS is_followup_eligible,
    c.observation_cutoff
FROM with_next AS w
CROSS JOIN cutoff AS c

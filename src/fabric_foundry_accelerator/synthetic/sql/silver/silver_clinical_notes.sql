-- Notes with original note_text preserved byte-for-byte. Literal backslash-n sequences are
-- flagged, not converted; any display conversion must be a separate, explicit step.
SELECT
    note_id,
    patient_id,
    encounter_id,
    CAST(try_strptime(note_date, '%Y-%m-%d') AS DATE) AS note_date,
    note_type,
    provider,
    note_text,
    strpos(note_text, chr(92) || 'n') > 0 AS has_literal_newline_sequence,
    strpos(note_text, chr(10)) > 0 AS has_embedded_newline
FROM bronze_clinical_notes

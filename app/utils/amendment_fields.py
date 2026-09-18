DOCTOR_AMENDABLE_FIELDS = {
    "documentation_mode",
    "free_text",
    "presenting_complaints",
    "hpc",
    "past_medical_history",
    "drug_history",
    "family_history",
    "review_of_systems",
    "general_examination",
    "cardiovascular_examination",
    "respiratory_examination",
    "abdominal_examination",
    "neurological_examination",
    "musculoskeletal_examination",
    "other_examination",
    "primary_diagnosis",
    "secondary_diagnoses",
    "differential_diagnosis",
    "plan_management",
}


NURSING_AMENDABLE_FIELDS = {
    "temperature",
    "systolic_bp",
    "diastolic_bp",
    "pulse_rate",
    "respiratory_rate",
    "oxygen_saturation",
    "weight_kg",
    "height_cm",
    "bmi",
    "nursing_note",
}


LABORATORY_AMENDABLE_FIELDS = {
    "result_text",
    "result_flag",
}


AMENDABLE_FIELDS = {
    "DOCTOR_DOCUMENTATION": DOCTOR_AMENDABLE_FIELDS,
    "NURSING_DOCUMENTATION": NURSING_AMENDABLE_FIELDS,
    "LABORATORY_RESULT": LABORATORY_AMENDABLE_FIELDS,
}
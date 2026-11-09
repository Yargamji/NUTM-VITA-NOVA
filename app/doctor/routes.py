from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from app.extensions import db
from app.models import (
    Encounter,
    DoctorDocumentation,
    Investigation,
    InvestigationRequest,
    LaboratoryResult,
    Patient,
    Prescription,
)
from app.services.doctor_service import (
    save_doctor_documentation,
    submit_doctor_documentation,
)
from app.services.doctor_orders_service import (
    save_consultation_orders,
    send_investigation_requests,
    send_medications_to_pharmacy,
)
from app.utils.authorization import role_required
from app.utils.roles import DOCTOR


doctor_bp = Blueprint(
    "doctor",
    __name__,
    url_prefix="/doctor",
)


# =========================================================
# DOCTOR DASHBOARD
# =========================================================

@doctor_bp.route("/dashboard")
@role_required(DOCTOR)
def dashboard():
    encounters = (
        Encounter.query
        .filter_by(status="OPEN")
        .order_by(Encounter.arrival_time.asc())
        .all()
    )

    return render_template(
        "doctor/dashboard.html",
        encounters=encounters,
    )


# =========================================================
# VIEW SUBMITTED CONSULTATION
# =========================================================

@doctor_bp.route("/documentation/<int:documentation_id>")
@role_required(DOCTOR)
def view_submitted_documentation(documentation_id):
    documentation = DoctorDocumentation.query.filter_by(
        doctor_documentation_id=documentation_id,
        status="SUBMITTED",
    ).first_or_404()

    encounter = documentation.encounter

    return render_template(
        "doctor/view_documentation.html",
        documentation=documentation,
        encounter=encounter,
        patient=encounter.patient,
    )


# =========================================================
# CONSULTATION HISTORY
# =========================================================

@doctor_bp.route("/consultation-history")
@role_required(DOCTOR)
def consultation_history():
    search_query = request.args.get("q", "").strip()

    query = (
        DoctorDocumentation.query
        .join(
            Encounter,
            DoctorDocumentation.encounter_id == Encounter.encounter_id,
        )
        .filter(DoctorDocumentation.status == "SUBMITTED")
        .order_by(DoctorDocumentation.submitted_at.desc())
    )

    if search_query:
        query = (
            query
            .join(
                Patient,
                Encounter.patient_id == Patient.patient_id,
            )
            .filter(
                db.or_(
                    Patient.full_name.ilike(f"%{search_query}%"),
                    Patient.clinic_id.ilike(f"%{search_query}%"),
                )
            )
        )

    documentations = query.all()

    return render_template(
        "doctor/consultation_history.html",
        documentations=documentations,
        search_query=search_query,
    )


# =========================================================
# CONSULTATION WORKSPACE
# =========================================================

@doctor_bp.route(
    "/encounters/<int:encounter_id>",
    methods=["GET", "POST"],
)
@role_required(DOCTOR)
def consultation_workspace(encounter_id):
    encounter = Encounter.query.get_or_404(encounter_id)

    if request.method == "POST":
        action = request.form.get("action")
        documentation_mode = request.form.get("documentation_mode")

        fields = {
            "free_text": request.form.get("free_text"),
            "presenting_complaints": request.form.get(
                "presenting_complaints"
            ),
            "hpc": request.form.get("hpc"),
            "past_medical_history": request.form.get(
                "past_medical_history"
            ),
            "drug_history": request.form.get("drug_history"),
            "family_history": request.form.get("family_history"),
            "review_of_systems": request.form.get(
                "review_of_systems"
            ),
            "general_examination": request.form.get(
                "general_examination"
            ),
            "cardiovascular_examination": request.form.get(
                "cardiovascular_examination"
            ),
            "respiratory_examination": request.form.get(
                "respiratory_examination"
            ),
            "abdominal_examination": request.form.get(
                "abdominal_examination"
            ),
            "neurological_examination": request.form.get(
                "neurological_examination"
            ),
            "musculoskeletal_examination": request.form.get(
                "musculoskeletal_examination"
            ),
            "other_examination": request.form.get(
                "other_examination"
            ),
            "primary_diagnosis": request.form.get(
                "primary_diagnosis"
            ),
            "secondary_diagnoses": request.form.get(
                "secondary_diagnoses"
            ),
            "differential_diagnosis": request.form.get(
                "differential_diagnosis"
            ),
            "plan_management": request.form.get(
                "plan_management"
            ),
        }

        investigation_ids = request.form.getlist(
            "investigation_ids"
        )

        investigation_information = request.form.getlist(
            "investigation_information"
        )

        medication_names = request.form.getlist("medication_name")
        medication_doses = request.form.getlist("medication_dose")
        medication_formulations = request.form.getlist(
            "medication_formulation"
        )
        medication_routes = request.form.getlist("medication_route")
        medication_frequencies = request.form.getlist(
            "medication_frequency"
        )
        medication_durations = request.form.getlist(
            "medication_duration"
        )
        medication_instructions = request.form.getlist(
            "medication_instructions"
        )

        medication_row_count = max(
            len(medication_names),
            len(medication_doses),
            len(medication_formulations),
            len(medication_routes),
            len(medication_frequencies),
            len(medication_durations),
            len(medication_instructions),
        )

        medication_items = []

        for index in range(medication_row_count):
            medication_items.append({
                "medication_name": (
                    medication_names[index]
                    if index < len(medication_names)
                    else ""
                ),
                "dose": (
                    medication_doses[index]
                    if index < len(medication_doses)
                    else ""
                ),
                "formulation": (
                    medication_formulations[index]
                    if index < len(medication_formulations)
                    else ""
                ),
                "route": (
                    medication_routes[index]
                    if index < len(medication_routes)
                    else ""
                ),
                "frequency": (
                    medication_frequencies[index]
                    if index < len(medication_frequencies)
                    else ""
                ),
                "duration": (
                    medication_durations[index]
                    if index < len(medication_durations)
                    else ""
                ),
                "instructions": (
                    medication_instructions[index]
                    if index < len(medication_instructions)
                    else ""
                ),
            })

        try:
            if action not in {
                "save",
                "submit",
                "send_investigations",
                "send_medications",
            }:
                raise ValueError("Invalid form action.")

            # Save the clinical note and send investigation requests.
            if action == "send_investigations":
                save_doctor_documentation(
                    encounter_id=encounter_id,
                    created_by=current_user.user_id,
                    documentation_mode=documentation_mode,
                    **fields,
                )

                send_investigation_requests(
                    encounter_id=encounter_id,
                    doctor_id=current_user.user_id,
                    investigation_ids=investigation_ids,
                    investigation_information=investigation_information,
                )

                flash(
                    "Investigation request(s) sent successfully. "
                    "The consultation remains open.",
                    "success",
                )

                return redirect(
                    url_for(
                        "doctor.consultation_workspace",
                        encounter_id=encounter_id,
                    )
                )

            # Save the clinical note and send prescriptions.
            if action == "send_medications":
                save_doctor_documentation(
                    encounter_id=encounter_id,
                    created_by=current_user.user_id,
                    documentation_mode=documentation_mode,
                    **fields,
                )

                send_medications_to_pharmacy(
                    encounter_id=encounter_id,
                    doctor_id=current_user.user_id,
                    medication_items=medication_items,
                )

                flash(
                    "Medication prescription sent successfully. "
                    "The consultation remains open.",
                    "success",
                )

                return redirect(
                    url_for(
                        "doctor.consultation_workspace",
                        encounter_id=encounter_id,
                    )
                )

            # Save the clinical documentation and order drafts.
            documentation = save_doctor_documentation(
                encounter_id=encounter_id,
                created_by=current_user.user_id,
                documentation_mode=documentation_mode,
                **fields,
            )

            save_consultation_orders(
                encounter_id=encounter_id,
                doctor_id=current_user.user_id,
                investigation_ids=investigation_ids,
                investigation_information=investigation_information,
                medication_items=medication_items,
            )

            if action == "save":
                flash(
                    "Clinical documentation and unsent order drafts "
                    "saved successfully.",
                    "success",
                )

                return redirect(
                    url_for(
                        "doctor.consultation_workspace",
                        encounter_id=encounter_id,
                    )
                )

            # Submit the consultation without automatically sending
            # or finalizing outstanding order drafts.
            submit_doctor_documentation(
                doctor_documentation_id=(
                    documentation.doctor_documentation_id
                ),
                submitted_by=current_user.user_id,
            )

            flash(
                "Consultation submitted successfully. "
                "Draft orders were not automatically sent.",
                "success",
            )

            return redirect(url_for("doctor.dashboard"))

        except (ValueError, PermissionError) as exc:
            db.session.rollback()
            flash(str(exc), "error")

        except Exception:
            db.session.rollback()
            flash(
                "Unable to complete the requested operation. "
                "Check the application terminal for details.",
                "error",
            )

    # Retrieve the current doctor's editable documentation draft.
    draft_documentation = (
        DoctorDocumentation.query
        .filter_by(
            encounter_id=encounter_id,
            created_by=current_user.user_id,
            status="DRAFT",
        )
        .order_by(DoctorDocumentation.created_at.desc())
        .first()
    )

    # Retrieve all documentation for the current encounter.
    doctor_documentations = (
        DoctorDocumentation.query
        .filter_by(encounter_id=encounter_id)
        .order_by(DoctorDocumentation.created_at.desc())
        .all()
    )

    active_investigations = (
        Investigation.query
        .filter_by(is_active=True)
        .order_by(Investigation.investigation_name.asc())
        .all()
    )

    # Retrieve this doctor's editable investigation drafts.
    draft_investigation_requests = (
        InvestigationRequest.query
        .filter_by(
            encounter_id=encounter_id,
            requested_by=current_user.user_id,
            status="DRAFT",
        )
        .order_by(InvestigationRequest.created_at.asc())
        .all()
    )

    # Retrieve submitted investigation requests, including their results.
    submitted_investigation_requests = (
        InvestigationRequest.query
        .filter(
            InvestigationRequest.encounter_id == encounter_id,
            InvestigationRequest.status != "DRAFT",
        )
        .order_by(InvestigationRequest.created_at.desc())
        .all()
    )

    # Retrieve this doctor's latest editable prescription draft.
    draft_prescription = (
        Prescription.query
        .filter_by(
            encounter_id=encounter_id,
            prescribed_by=current_user.user_id,
            status="DRAFT",
        )
        .order_by(Prescription.prescribed_at.desc())
        .first()
    )

    # Retrieve submitted prescriptions for read-only display.
    submitted_prescriptions = (
        Prescription.query
        .filter(
            Prescription.encounter_id == encounter_id,
            Prescription.status != "DRAFT",
        )
        .order_by(Prescription.prescribed_at.desc())
        .all()
    )

    return render_template(
        "doctor/consultation.html",
        encounter=encounter,
        patient=encounter.patient,
        nursing_documentations=encounter.nursing_documentations,
        doctor_documentations=doctor_documentations,
        draft_documentation=draft_documentation,
        active_investigations=active_investigations,
        draft_investigation_requests=draft_investigation_requests,
        submitted_investigation_requests=submitted_investigation_requests,
        draft_prescription=draft_prescription,
        submitted_prescriptions=submitted_prescriptions,
    )


# =========================================================
# LONGITUDINAL LABORATORY RESULTS
# =========================================================

@doctor_bp.route("/patients/<int:patient_id>/lab-results")
@role_required(DOCTOR)
def patient_lab_results(patient_id):
    """
    Display all finalized laboratory results for a patient
    across all encounters, newest first.
    """

    patient = Patient.query.get_or_404(patient_id)

    laboratory_results = (
        LaboratoryResult.query
        .join(
            InvestigationRequest,
            LaboratoryResult.investigation_request_id
            == InvestigationRequest.investigation_request_id,
        )
        .join(
            Encounter,
            InvestigationRequest.encounter_id == Encounter.encounter_id,
        )
        .filter(
            Encounter.patient_id == patient.patient_id,
            LaboratoryResult.status == "FINALIZED",
        )
        .order_by(
            LaboratoryResult.finalized_at.desc(),
            LaboratoryResult.created_at.desc(),
        )
        .all()
    )

    return render_template(
        "doctor/patient_lab_results.html",
        patient=patient,
        laboratory_results=laboratory_results,
    )
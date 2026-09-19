from datetime import datetime

from flask_login import UserMixin

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.role_id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    role = db.relationship("Role", back_populates="users")

    encounters_created = db.relationship(
        "Encounter",
        back_populates="creator",
    )

    nursing_documentations = db.relationship(
        "NursingDocumentation",
        back_populates="author",
    )
    medication_administrations = db.relationship(
        "MedicationAdministration",
        back_populates="administrator",
    )
    doctor_documentations = db.relationship(
        "DoctorDocumentation",
        back_populates="author",
    )

    investigations_created = db.relationship(
        "Investigation",
        back_populates="creator",
    )

    investigation_requests = db.relationship(
        "InvestigationRequest",
        back_populates="requester",
    )

    laboratory_results_created = db.relationship(
        "LaboratoryResult",
        foreign_keys="LaboratoryResult.created_by",
        back_populates="creator",
    )

    laboratory_results_finalized = db.relationship(
        "LaboratoryResult",
        foreign_keys="LaboratoryResult.finalized_by",
        back_populates="finalizer",
    )

    prescriptions_created = db.relationship(
        "Prescription",
        foreign_keys="Prescription.prescribed_by",
        back_populates="prescriber",
    )

    prescriptions_finalized = db.relationship(
        "Prescription",
        foreign_keys="Prescription.finalized_by",
        back_populates="finalizer",
    )

    pharmacy_communications = db.relationship(
    "PharmacyCommunication",
    back_populates="sender",
)
    pharmacy_dispensings = db.relationship(
    "PharmacyDispensing",
    back_populates="dispenser",
)

    record_amendments = db.relationship(
    "RecordAmendment",
    foreign_keys="RecordAmendment.amended_by",
    back_populates="amended_by_user",
)
    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return f"<User {self.phone_number}>"
    
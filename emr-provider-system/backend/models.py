from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from database import Base
import datetime
from constants import (
    MAX_LENGTH_PRACTITIONER_CODE,
    MAX_LENGTH_FULL_NAME,
    MAX_LENGTH_SPECIALTY,
    MAX_LENGTH_PHONE,
    MAX_LENGTH_PATIENT_EXTERNAL_ID,
    MAX_LENGTH_NATIONAL_ID,
    MAX_LENGTH_GENDER,
    MAX_LENGTH_INSURANCE_CARD_NO,
    MAX_LENGTH_STATUS,
    MAX_LENGTH_LOCATION,
    MAX_LENGTH_CATEGORY,
    MAX_LENGTH_CODE_DISPLAY,
    MAX_LENGTH_CODE_SYSTEM,
    MAX_LENGTH_VALUE_UNIT,
    GENDER_CHOICES,
    DEFAULT_ENCOUNTER_STATUS,
)


class Practitioner(Base):
    __tablename__ = "practitioners"

    id = Column(Integer, primary_key=True, index=True)
    # Mã nhân viên y tế
    practitioner_code = Column(
        String(MAX_LENGTH_PRACTITIONER_CODE), unique=True, nullable=False, index=True
    )
    full_name = Column(String(MAX_LENGTH_FULL_NAME), nullable=False)
    specialty = Column(String(MAX_LENGTH_SPECIALTY))  # Chuyên khoa
    phone = Column(String(MAX_LENGTH_PHONE))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    encounters = relationship("Encounter", back_populates="practitioner")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    # Mã BN tại bệnh viện
    patient_external_id = Column(
        String(MAX_LENGTH_PATIENT_EXTERNAL_ID), unique=True, nullable=False, index=True
    )
    # Số CCCD (Định danh quốc gia)
    national_id = Column(String(MAX_LENGTH_NATIONAL_ID), unique=True)
    full_name = Column(String(MAX_LENGTH_FULL_NAME), nullable=False)
    gender = Column(String(MAX_LENGTH_GENDER))
    birth_date = Column(Date, nullable=False)
    address = Column(Text)
    phone = Column(String(MAX_LENGTH_PHONE))
    # Mã số thẻ BHYT
    insurance_card_no = Column(String(MAX_LENGTH_INSURANCE_CARD_NO))
    is_deleted = Column(Boolean, default=False)
    # Relationships
    encounters = relationship("Encounter", back_populates="patient")

    __table_args__ = (CheckConstraint(gender.in_(GENDER_CHOICES), name="check_gender"),)


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"))
    status = Column(String(MAX_LENGTH_STATUS), default=DEFAULT_ENCOUNTER_STATUS)
    start_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    reason_code = Column(Text)  # Lý do khám/Mã ICD-10 sơ bộ
    location = Column(String(MAX_LENGTH_LOCATION))  # Phòng khám/Khoa
    is_deleted = Column(Boolean, default=False)

    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    practitioner = relationship("Practitioner", back_populates="encounters")
    observations = relationship("Observation", back_populates="encounter")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"))
    category = Column(String(MAX_LENGTH_CATEGORY))
    # Tên chỉ số: "Huyết áp tâm thu", "Cân nặng"
    code_display = Column(String(MAX_LENGTH_CODE_DISPLAY))
    # Mã chuẩn (LOINC) nếu có
    code_system = Column(String(MAX_LENGTH_CODE_SYSTEM))
    value_number = Column(Numeric)
    # mmHg, kg, Celsius
    value_unit = Column(String(MAX_LENGTH_VALUE_UNIT))
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    encounter = relationship("Encounter", back_populates="observations")

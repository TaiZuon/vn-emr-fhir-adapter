from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from constants import (
    MAX_LENGTH_PRACTITIONER_CODE,
    MAX_LENGTH_FULL_NAME,
    MAX_LENGTH_SPECIALTY,
    MAX_LENGTH_PHONE,
    MAX_LENGTH_PATIENT_EXTERNAL_ID,
    MAX_LENGTH_NATIONAL_ID,
    MAX_LENGTH_INSURANCE_CARD_NO,
    MAX_LENGTH_LOCATION,
    MAX_LENGTH_CATEGORY,
    MAX_LENGTH_CODE_DISPLAY,
    MAX_LENGTH_CODE_SYSTEM,
    MAX_LENGTH_VALUE_UNIT,
    GENDER_MALE,
    GENDER_FEMALE,
    GENDER_OTHER,
    ENCOUNTER_STATUS_PLANNED,
    ENCOUNTER_STATUS_ARRIVED,
    ENCOUNTER_STATUS_FINISHED,
    DEFAULT_ENCOUNTER_STATUS,
)


# Enums
class GenderEnum(str, Enum):
    male = GENDER_MALE
    female = GENDER_FEMALE
    other = GENDER_OTHER


class EncounterStatusEnum(str, Enum):
    planned = ENCOUNTER_STATUS_PLANNED
    arrived = ENCOUNTER_STATUS_ARRIVED
    finished = ENCOUNTER_STATUS_FINISHED


# Practitioner Schemas


class PractitionerBase(BaseModel):
    practitioner_code: str = Field(
        ..., max_length=MAX_LENGTH_PRACTITIONER_CODE, description="Mã nhân viên y tế"
    )
    full_name: str = Field(..., max_length=MAX_LENGTH_FULL_NAME)
    specialty: Optional[str] = Field(
        None, max_length=MAX_LENGTH_SPECIALTY, description="Chuyên khoa"
    )
    phone: Optional[str] = Field(None, max_length=MAX_LENGTH_PHONE)


class PractitionerCreate(PractitionerBase):
    pass


class PractitionerUpdate(BaseModel):
    practitioner_code: Optional[str] = Field(
        None, max_length=MAX_LENGTH_PRACTITIONER_CODE
    )
    full_name: Optional[str] = Field(None, max_length=MAX_LENGTH_FULL_NAME)
    specialty: Optional[str] = Field(None, max_length=MAX_LENGTH_SPECIALTY)
    phone: Optional[str] = Field(None, max_length=MAX_LENGTH_PHONE)


class PractitionerResponse(PractitionerBase):
    id: int

    class Config:
        from_attributes = True


# Patient Schemas


class PatientBase(BaseModel):
    patient_external_id: str = Field(
        ...,
        max_length=MAX_LENGTH_PATIENT_EXTERNAL_ID,
        description="Mã BN tại bệnh viện",
    )
    national_id: Optional[str] = Field(
        None, max_length=MAX_LENGTH_NATIONAL_ID, description="Số CCCD"
    )
    full_name: str = Field(..., max_length=MAX_LENGTH_FULL_NAME)
    gender: Optional[GenderEnum] = None
    birth_date: date
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=MAX_LENGTH_PHONE)
    insurance_card_no: Optional[str] = Field(
        None, max_length=MAX_LENGTH_INSURANCE_CARD_NO, description="Mã số thẻ BHYT"
    )


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    patient_external_id: Optional[str] = Field(
        None, max_length=MAX_LENGTH_PATIENT_EXTERNAL_ID
    )
    national_id: Optional[str] = Field(None, max_length=MAX_LENGTH_NATIONAL_ID)
    full_name: Optional[str] = Field(None, max_length=MAX_LENGTH_FULL_NAME)
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=MAX_LENGTH_PHONE)
    insurance_card_no: Optional[str] = Field(
        None, max_length=MAX_LENGTH_INSURANCE_CARD_NO
    )


class PatientResponse(PatientBase):
    id: int

    class Config:
        from_attributes = True


# Observation Schemas


class ObservationBase(BaseModel):
    category: Optional[str] = Field(
        None,
        max_length=MAX_LENGTH_CATEGORY,
        description="vital-signs, laboratory, etc.",
    )
    code_display: Optional[str] = Field(
        None, max_length=MAX_LENGTH_CODE_DISPLAY, description="Tên chỉ số"
    )
    code_system: Optional[str] = Field(
        None, max_length=MAX_LENGTH_CODE_SYSTEM, description="Mã chuẩn LOINC"
    )
    value_number: Optional[Decimal] = None
    value_unit: Optional[str] = Field(
        None, max_length=MAX_LENGTH_VALUE_UNIT, description="mmHg, kg, Celsius"
    )


class ObservationCreate(ObservationBase):
    encounter_id: int


class ObservationUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=MAX_LENGTH_CATEGORY)
    code_display: Optional[str] = Field(None, max_length=MAX_LENGTH_CODE_DISPLAY)
    code_system: Optional[str] = Field(None, max_length=MAX_LENGTH_CODE_SYSTEM)
    value_number: Optional[Decimal] = None
    value_unit: Optional[str] = Field(None, max_length=MAX_LENGTH_VALUE_UNIT)


class ObservationResponse(ObservationBase):
    id: int
    encounter_id: int
    issued_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Encounter Schemas


class EncounterBase(BaseModel):
    patient_id: int
    practitioner_id: Optional[int] = None
    status: Optional[EncounterStatusEnum] = EncounterStatusEnum(
        DEFAULT_ENCOUNTER_STATUS
    )
    reason_code: Optional[str] = Field(None, description="Lý do khám/Mã ICD-10 sơ bộ")
    location: Optional[str] = Field(
        None, max_length=MAX_LENGTH_LOCATION, description="Phòng khám/Khoa"
    )


class EncounterCreate(EncounterBase):
    pass


class EncounterUpdate(BaseModel):
    patient_id: Optional[int] = None
    practitioner_id: Optional[int] = None
    status: Optional[EncounterStatusEnum] = None
    reason_code: Optional[str] = None
    location: Optional[str] = Field(None, max_length=MAX_LENGTH_LOCATION)


class EncounterResponse(EncounterBase):
    id: int
    start_timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class EncounterWithRelations(EncounterResponse):
    """Encounter với thông tin Patient, Practitioner và Observations"""

    patient: Optional[PatientResponse] = None
    practitioner: Optional[PractitionerResponse] = None
    observations: List[ObservationResponse] = []

    class Config:
        from_attributes = True


# Patient với Encounters


class PatientWithEncounters(PatientResponse):
    """Patient với danh sách các lượt khám"""

    encounters: List[EncounterResponse] = []

    class Config:
        from_attributes = True


# Practitioner với Encounters


class PractitionerWithEncounters(PractitionerResponse):
    """Practitioner với danh sách các lượt khám"""

    encounters: List[EncounterResponse] = []

    class Config:
        from_attributes = True

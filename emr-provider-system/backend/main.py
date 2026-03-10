from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
import database
import publisher
from constants import API_TITLE, EVENT_PATIENT_CREATED, RABBITMQ_QUEUE_NAME

app = FastAPI(title=API_TITLE)


@app.post("/patients/", response_model=schemas.PatientResponse)
def create_patient(
    patient: schemas.PatientCreate, db: Session = Depends(database.get_db)
):
    # Lưu vào SQL
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    # Bắn sự kiện sang RabbitMQ (Task 2.2)
    event_data = {
        "event_type": EVENT_PATIENT_CREATED,
        "patient_id": db_patient.id,
        "external_id": db_patient.patient_external_id,
    }
    publisher.publish_event(RABBITMQ_QUEUE_NAME, event_data)

    return db_patient

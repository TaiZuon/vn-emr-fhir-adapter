-- Bảng bác sĩ (Practitioner)
CREATE TABLE practitioners (
    id SERIAL PRIMARY KEY,
    practitioner_code VARCHAR(20) UNIQUE NOT NULL, -- Mã nhân viên y tế
    full_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),                        -- Chuyên khoa
    phone VARCHAR(20)
);

-- Bảng bệnh nhân (Patient)
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    patient_external_id VARCHAR(50) UNIQUE NOT NULL, -- Mã BN tại bệnh viện
    national_id VARCHAR(12) UNIQUE,                 -- Số CCCD (Định danh quốc gia)
    full_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('Nam', 'Nữ', 'Khác')),
    birth_date DATE NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    insurance_card_no VARCHAR(15)                   -- Mã số thẻ BHYT
);

-- Bảng lượt khám (Encounter)
CREATE TABLE encounters (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    practitioner_id INTEGER REFERENCES practitioners(id),
    status VARCHAR(20) DEFAULT 'finished',           -- planned, arrived, finished
    start_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason_code TEXT,                                -- Lý do khám/Mã ICD-10 sơ bộ
    location VARCHAR(100)                            -- Phòng khám/Khoa
);

-- Bảng chỉ số sinh tồn/Xét nghiệm (Observation)
CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    encounter_id INTEGER REFERENCES encounters(id),
    category VARCHAR(50),      -- vital-signs, laboratory, etc.
    code_display VARCHAR(100), -- Tên chỉ số: "Huyết áp tâm thu", "Cân nặng"
    code_system VARCHAR(100),  -- Mã chuẩn (LOINC) nếu có
    value_number DECIMAL,
    value_unit VARCHAR(20),    -- mmHg, kg, Celsius
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

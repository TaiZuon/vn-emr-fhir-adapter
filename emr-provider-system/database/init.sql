-- Bảng nhân viên y tế (nhan_vien_y_te)
CREATE TABLE nhan_vien_y_te (
    id SERIAL PRIMARY KEY,
    ma_bac_si VARCHAR(20) UNIQUE NOT NULL,
    ho_ten VARCHAR(100) NOT NULL,
    chuyen_khoa VARCHAR(100),
    so_dien_thoai VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Bảng bệnh nhân (benh_nhan)
CREATE TABLE benh_nhan (
    id SERIAL PRIMARY KEY,
    ma_bn VARCHAR(50) UNIQUE NOT NULL,
    ho_ten VARCHAR(100) NOT NULL,
    ngay_sinh DATE NOT NULL,
    gioi_tinh INT CHECK (gioi_tinh IN (1, 2, 3)), -- 1: Nam, 2: Nữ, 3: Không xác định
    dia_chi TEXT,
    cccd VARCHAR(12) UNIQUE,
    can_nang DECIMAL,
    ten_nguoi_dua_tre_den VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    chu_ky_so TEXT
);

-- Bảng đợt điều trị (dot_dieu_tri)
CREATE TABLE dot_dieu_tri (
    ma_lk VARCHAR(50) PRIMARY KEY, -- Primary Key or Unique
    benh_nhan_id INTEGER REFERENCES benh_nhan(id),
    ma_bac_si VARCHAR(20) REFERENCES nhan_vien_y_te(ma_bac_si),
    ma_the VARCHAR(50),
    ma_dkbd VARCHAR(20),
    gt_the_tu DATE,
    gt_the_den DATE,
    mien_cung_ct DATE,
    ngay_vao TIMESTAMP,
    ngay_ra TIMESTAMP,
    ma_benh VARCHAR(20),
    ma_benh_khac VARCHAR(200),
    ten_benh TEXT,
    ket_qua_dtri INT,
    tinh_trang_rv INT,
    t_tongchi DECIMAL,
    t_bhtt DECIMAL,
    t_bntt DECIMAL,
    t_bncct DECIMAL,
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Bảng chi tiết thuốc (chi_tiet_thuoc)
CREATE TABLE chi_tiet_thuoc (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(50) REFERENCES dot_dieu_tri(ma_lk),
    ma_don_thuoc VARCHAR(20), -- 14 chars format: xxxxxyyyyyyy-z
    stt INT,
    ma_thuoc VARCHAR(50),
    ten_thuoc VARCHAR(200),
    don_vi_tinh VARCHAR(20),
    ham_luong VARCHAR(50),
    duong_dung VARCHAR(50),
    lieu_dung VARCHAR(100),
    so_luong DECIMAL,
    don_gia DECIMAL,
    thanh_tien DECIMAL,
    ma_bac_si VARCHAR(20),
    ngay_yl TIMESTAMP,
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Bảng dịch vụ kỹ thuật (dich_vu_ky_thuat)
CREATE TABLE dich_vu_ky_thuat (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(50) REFERENCES dot_dieu_tri(ma_lk),
    stt INT,
    ma_dich_vu VARCHAR(50),
    ten_dich_vu VARCHAR(200),
    ma_vat_tu VARCHAR(50),
    ten_vat_tu VARCHAR(200),
    so_luong DECIMAL,
    don_gia DECIMAL,
    thanh_tien DECIMAL,
    ma_khoa VARCHAR(50),
    ma_giuong VARCHAR(50),
    ma_bac_si VARCHAR(20),
    ngay_yl TIMESTAMP,
    ngay_kq TIMESTAMP,
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Bảng cận lâm sàng (can_lam_sang)
CREATE TABLE can_lam_sang (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(50) REFERENCES dot_dieu_tri(ma_lk),
    stt INT,
    ma_dich_vu VARCHAR(50),
    ma_chi_so VARCHAR(50),
    ten_chi_so VARCHAR(200),
    gia_tri VARCHAR(100),
    ma_may VARCHAR(50),
    mo_ta TEXT,
    ket_luan TEXT,
    ngay_kq TIMESTAMP,
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Bảng diễn biến lâm sàng (dien_bien_lam_sang)
CREATE TABLE dien_bien_lam_sang (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(50) REFERENCES dot_dieu_tri(ma_lk),
    stt INT,
    dien_bien TEXT,
    hoi_chan TEXT,
    phau_thuat TEXT,
    ngay_yl TIMESTAMP,
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

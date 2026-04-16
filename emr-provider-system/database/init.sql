-- 1. Bảng nhân viên y tế (nhan_vien_y_te)
CREATE TABLE nhan_vien_y_te (
    id SERIAL PRIMARY KEY,
    ma_bac_si VARCHAR(255) UNIQUE NOT NULL,
    ho_ten VARCHAR(255) NOT NULL,
    chuyen_khoa VARCHAR(255),
    so_dien_thoai VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 2. Bảng bệnh nhân (benh_nhan)
CREATE TABLE benh_nhan (
    id SERIAL PRIMARY KEY,
    ma_bn VARCHAR(100) UNIQUE NOT NULL,
    ho_ten VARCHAR(255) NOT NULL,
    ngay_sinh VARCHAR(12) NOT NULL,          -- Định dạng yyyymmddHHMM
    gioi_tinh INT CHECK (gioi_tinh IN (1, 2, 3)), -- 1: Nam, 2: Nữ, 3: Không xác định
    dia_chi VARCHAR(1024),
    cccd VARCHAR(15) UNIQUE,
    can_nang DECIMAL(5,2),
    ten_nguoi_dua_tre_den VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    chu_ky_so TEXT
);

-- 3. Bảng đợt điều trị (dot_dieu_tri) - Tương ứng XML1
CREATE TABLE dot_dieu_tri (
    ma_lk VARCHAR(100) PRIMARY KEY,
    benh_nhan_id INTEGER REFERENCES benh_nhan(id),
    ma_bac_si VARCHAR(255) REFERENCES nhan_vien_y_te(ma_bac_si),
    ma_the VARCHAR(15),
    ma_dkbd VARCHAR(5),
    gt_the_tu VARCHAR(12),
    gt_the_den VARCHAR(12),
    mien_cung_ct VARCHAR(12),
    ngay_vao VARCHAR(12),
    ngay_ra VARCHAR(12),
    ma_benh VARCHAR(20),
    ma_benh_khac TEXT,
    ten_benh TEXT,
    ket_qua_dtri INT,
    tinh_trang_rv INT,
    t_tongchi DECIMAL(15,2),
    t_bhtt DECIMAL(15,2),
    t_bntt DECIMAL(15,2),
    t_bncct DECIMAL(15,2),
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 4. Bảng chi tiết thuốc (chi_tiet_thuoc) - Tương ứng XML2
CREATE TABLE chi_tiet_thuoc (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(100) REFERENCES dot_dieu_tri(ma_lk),
    ma_don_thuoc VARCHAR(20),
    stt INT,
    ma_thuoc VARCHAR(255),
    ten_thuoc VARCHAR(1024),
    don_vi_tinh VARCHAR(50),
    ham_luong VARCHAR(1024),
    duong_dung VARCHAR(4),
    lieu_dung VARCHAR(1024),
    so_luong DECIMAL(15,3),
    don_gia DECIMAL(15,3),
    thanh_tien DECIMAL(15,2),
    ma_bac_si VARCHAR(255),
    ngay_yl VARCHAR(12),
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 5. Bảng dịch vụ kỹ thuật (dich_vu_ky_thuat) - Tương ứng XML3
CREATE TABLE dich_vu_ky_thuat (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(100) REFERENCES dot_dieu_tri(ma_lk),
    stt INT,
    ma_dich_vu VARCHAR(255),
    ten_dich_vu VARCHAR(1024),
    ma_vat_tu VARCHAR(255),
    ten_vat_tu VARCHAR(1024),
    so_luong DECIMAL(15,3),
    don_gia DECIMAL(15,3),
    thanh_tien DECIMAL(15,2),
    ma_khoa VARCHAR(15),
    ma_giuong VARCHAR(50),
    ma_bac_si VARCHAR(255),
    ngay_yl VARCHAR(12),
    ngay_kq VARCHAR(12),
    ma_may VARCHAR(1024),
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 6. Bảng cận lâm sàng (can_lam_sang) - Tương ứng XML4
CREATE TABLE can_lam_sang (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(100) REFERENCES dot_dieu_tri(ma_lk),
    stt INT,
    ma_dich_vu VARCHAR(255),
    ma_chi_so VARCHAR(50),
    ten_chi_so VARCHAR(255),
    gia_tri VARCHAR(255),
    ma_may VARCHAR(1024),
    mo_ta TEXT,
    ket_luan TEXT,
    ngay_kq VARCHAR(12),
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 7. Bảng diễn biến lâm sàng (dien_bien_lam_sang) - Tương ứng XML5
CREATE TABLE dien_bien_lam_sang (
    id SERIAL PRIMARY KEY,
    dot_dieu_tri_id VARCHAR(100) REFERENCES dot_dieu_tri(ma_lk),
    stt INT,
    dien_bien TEXT,
    hoi_chan TEXT,
    phau_thuat TEXT,
    ngay_yl VARCHAR(12),
    chu_ky_so TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

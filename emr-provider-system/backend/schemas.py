from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class NhanVienYTeBase(BaseModel):
    ma_bac_si: str = Field(..., max_length=20)
    ho_ten: str = Field(..., max_length=100)
    chuyen_khoa: Optional[str] = Field(None, max_length=100)
    so_dien_thoai: Optional[str] = Field(None, max_length=20)

class NhanVienYTeCreate(NhanVienYTeBase):
    pass

class NhanVienYTeSchema(NhanVienYTeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class BenhNhanBase(BaseModel):
    ma_bn: str = Field(..., max_length=50)
    ho_ten: str = Field(..., max_length=100)
    ngay_sinh: date
    gioi_tinh: int
    dia_chi: Optional[str] = None
    cccd: Optional[str] = Field(None, max_length=12)
    can_nang: Optional[float] = None
    ten_nguoi_dua_tre_den: Optional[str] = Field(None, max_length=100)
    chu_ky_so: Optional[str] = None

class BenhNhanCreate(BenhNhanBase):
    pass

class BenhNhanSchema(BenhNhanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class DotDieuTriBase(BaseModel):
    ma_lk: str = Field(..., max_length=50)
    benh_nhan_id: int
    ma_bac_si: Optional[str] = Field(None, max_length=20)
    ma_the: Optional[str] = Field(None, max_length=50)
    ma_dkbd: Optional[str] = Field(None, max_length=20)
    gt_the_tu: Optional[date] = None
    gt_the_den: Optional[date] = None
    mien_cung_ct: Optional[date] = None
    ngay_vao: Optional[datetime] = None
    ngay_ra: Optional[datetime] = None
    ma_benh: Optional[str] = Field(None, max_length=20)
    ma_benh_khac: Optional[str] = Field(None, max_length=200)
    ten_benh: Optional[str] = None
    ket_qua_dtri: Optional[int] = None
    tinh_trang_rv: Optional[int] = None
    t_tongchi: Optional[float] = None
    t_bhtt: Optional[float] = None
    t_bntt: Optional[float] = None
    t_bncct: Optional[float] = None
    chu_ky_so: Optional[str] = None

class DotDieuTriCreate(DotDieuTriBase):
    pass

class DotDieuTriSchema(DotDieuTriBase):
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ChiTietThuocBase(BaseModel):
    dot_dieu_tri_id: str = Field(..., max_length=50)
    ma_don_thuoc: Optional[str] = Field(None, max_length=20)
    stt: Optional[int] = None
    ma_thuoc: Optional[str] = Field(None, max_length=50)
    ten_thuoc: Optional[str] = Field(None, max_length=200)
    don_vi_tinh: Optional[str] = Field(None, max_length=20)
    ham_luong: Optional[str] = Field(None, max_length=50)
    duong_dung: Optional[str] = Field(None, max_length=50)
    lieu_dung: Optional[str] = Field(None, max_length=100)
    so_luong: Optional[float] = None
    don_gia: Optional[float] = None
    thanh_tien: Optional[float] = None
    ma_bac_si: Optional[str] = Field(None, max_length=20)
    ngay_yl: Optional[datetime] = None
    chu_ky_so: Optional[str] = None

class ChiTietThuocCreate(ChiTietThuocBase):
    pass

class ChiTietThuocSchema(ChiTietThuocBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class DichVuKyThuatBase(BaseModel):
    dot_dieu_tri_id: str = Field(..., max_length=50)
    stt: Optional[int] = None
    ma_dich_vu: Optional[str] = Field(None, max_length=50)
    ten_dich_vu: Optional[str] = Field(None, max_length=200)
    ma_vat_tu: Optional[str] = Field(None, max_length=50)
    ten_vat_tu: Optional[str] = Field(None, max_length=200)
    so_luong: Optional[float] = None
    don_gia: Optional[float] = None
    thanh_tien: Optional[float] = None
    ma_khoa: Optional[str] = Field(None, max_length=50)
    ma_giuong: Optional[str] = Field(None, max_length=50)
    ma_bac_si: Optional[str] = Field(None, max_length=20)
    ngay_yl: Optional[datetime] = None
    ngay_kq: Optional[datetime] = None
    chu_ky_so: Optional[str] = None

class DichVuKyThuatCreate(DichVuKyThuatBase):
    pass

class DichVuKyThuatSchema(DichVuKyThuatBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class CanLamSangBase(BaseModel):
    dot_dieu_tri_id: str = Field(..., max_length=50)
    stt: Optional[int] = None
    ma_dich_vu: Optional[str] = Field(None, max_length=50)
    ma_chi_so: Optional[str] = Field(None, max_length=50)
    ten_chi_so: Optional[str] = Field(None, max_length=200)
    gia_tri: Optional[str] = Field(None, max_length=100)
    ma_may: Optional[str] = Field(None, max_length=50)
    mo_ta: Optional[str] = None
    ket_luan: Optional[str] = None
    ngay_kq: Optional[datetime] = None
    chu_ky_so: Optional[str] = None

class CanLamSangCreate(CanLamSangBase):
    pass

class CanLamSangSchema(CanLamSangBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class DienBienLamSangBase(BaseModel):
    dot_dieu_tri_id: str = Field(..., max_length=50)
    stt: Optional[int] = None
    dien_bien: Optional[str] = None
    hoi_chan: Optional[str] = None
    phau_thuat: Optional[str] = None
    ngay_yl: Optional[datetime] = None
    chu_ky_so: Optional[str] = None

class DienBienLamSangCreate(DienBienLamSangBase):
    pass

class DienBienLamSangSchema(DienBienLamSangBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


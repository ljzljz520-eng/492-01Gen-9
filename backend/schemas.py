from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    full_name: str
    role: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StationBase(BaseModel):
    name: str
    address: str
    contact: Optional[str] = None
    phone: Optional[str] = None


class StationCreate(StationBase):
    pass


class StationUpdate(StationBase):
    pass


class StationResponse(StationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChargingGunBase(BaseModel):
    gun_number: str
    status: Optional[str] = "online"


class ChargingGunCreate(ChargingGunBase):
    pass


class ChargingGunResponse(ChargingGunBase):
    id: int
    charger_id: int
    last_check_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChargerBase(BaseModel):
    serial_number: str
    model: Optional[str] = None
    total_guns: Optional[int] = 2


class ChargerCreate(ChargerBase):
    station_id: int
    guns: List[ChargingGunCreate] = []


class ChargerResponse(ChargerBase):
    id: int
    station_id: int
    created_at: datetime
    guns: List[ChargingGunResponse] = []

    class Config:
        from_attributes = True


class StationDetailResponse(StationResponse):
    chargers: List[ChargerResponse] = []


class WorkOrderBase(BaseModel):
    order_type: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "normal"
    gun_id: Optional[int] = None
    take_gun_offline: Optional[bool] = False


class WorkOrderCreate(WorkOrderBase):
    assignee_id: Optional[int] = None


class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    description: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    id: int
    order_no: str
    status: str
    creator_id: int
    assignee_id: Optional[int] = None
    creator: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    gun: Optional[ChargingGunResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepairRecordBase(BaseModel):
    voltage_measurement: Optional[float] = None
    parts_replaced: Optional[bool] = False
    parts_description: Optional[str] = None
    repair_description: Optional[str] = None
    photo_urls: Optional[str] = None


class RepairRecordCreate(RepairRecordBase):
    work_order_id: int


class RepairRecordResponse(RepairRecordBase):
    id: int
    work_order_id: int
    repairer_id: int
    arrive_time: datetime
    repairer: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkOrderDetailResponse(WorkOrderResponse):
    repair_records: List[RepairRecordResponse] = []


class DashboardStats(BaseModel):
    total_orders: int
    pending_orders: int
    in_progress_orders: int
    completed_orders: int
    online_guns: int
    offline_guns: int
    total_stations: int

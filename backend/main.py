import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal, engine, Base
from models import User, Station, Charger, ChargingGun, WorkOrder, RepairRecord
from schemas import (
    Token, UserCreate, UserLogin, UserResponse,
    StationCreate, StationUpdate, StationResponse, StationDetailResponse,
    ChargerCreate, ChargerResponse,
    ChargingGunResponse,
    WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse, WorkOrderDetailResponse,
    RepairRecordCreate, RepairRecordResponse,
    DashboardStats
)
from auth import (
    get_db, verify_password, get_password_hash, create_access_token,
    get_current_user, require_role, ACCESS_TOKEN_EXPIRE_MINUTES
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="新能源充电桩巡检派单系统 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def generate_order_no() -> str:
    return f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"


def init_default_data(db: Session):
    if db.query(User).count() == 0:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="系统管理员",
            role="admin"
        )
        supervisor = User(
            username="supervisor",
            hashed_password=get_password_hash("super123"),
            full_name="张主管",
            role="supervisor"
        )
        repairer1 = User(
            username="repairer1",
            hashed_password=get_password_hash("repair123"),
            full_name="李维修",
            role="repairer"
        )
        repairer2 = User(
            username="repairer2",
            hashed_password=get_password_hash("repair456"),
            full_name="王师傅",
            role="repairer"
        )
        db.add_all([admin, supervisor, repairer1, repairer2])

        station1 = Station(
            name="朝阳公园充电站",
            address="北京市朝阳区朝阳公园南路1号",
            contact="刘经理",
            phone="13800138001"
        )
        station2 = Station(
            name="海淀中关村充电站",
            address="北京市海淀区中关村大街1号",
            contact="陈主任",
            phone="13800138002"
        )
        db.add_all([station1, station2])
        db.flush()

        charger1 = Charger(
            station_id=station1.id,
            serial_number="CHA001",
            model="DC-120KW",
            total_guns=2
        )
        charger2 = Charger(
            station_id=station1.id,
            serial_number="CHA002",
            model="DC-120KW",
            total_guns=2
        )
        charger3 = Charger(
            station_id=station2.id,
            serial_number="CHB001",
            model="DC-180KW",
            total_guns=2
        )
        db.add_all([charger1, charger2, charger3])
        db.flush()

        guns = [
            ChargingGun(charger_id=charger1.id, gun_number="A01", status="online"),
            ChargingGun(charger_id=charger1.id, gun_number="A02", status="online"),
            ChargingGun(charger_id=charger2.id, gun_number="B01", status="online"),
            ChargingGun(charger_id=charger2.id, gun_number="B02", status="online"),
            ChargingGun(charger_id=charger3.id, gun_number="C01", status="online"),
            ChargingGun(charger_id=charger3.id, gun_number="C02", status="offline"),
        ]
        db.add_all(guns)
        db.commit()


with SessionLocal() as db:
    init_default_data(db)


@app.post("/api/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/users", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()


@app.post("/api/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/stations", response_model=List[StationDetailResponse])
def list_stations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Station).all()


@app.get("/api/stations/{station_id}", response_model=StationDetailResponse)
def get_station(station_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="站点不存在")
    return station


@app.post("/api/stations", response_model=StationResponse)
def create_station(
    station_data: StationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor"))
):
    existing = db.query(Station).filter(Station.name == station_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="站点名称已存在")
    station = Station(**station_data.dict())
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


@app.put("/api/stations/{station_id}", response_model=StationResponse)
def update_station(
    station_id: int,
    station_data: StationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor"))
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="站点不存在")
    for key, value in station_data.dict(exclude_unset=True).items():
        setattr(station, key, value)
    db.commit()
    db.refresh(station)
    return station


@app.post("/api/chargers", response_model=ChargerResponse)
def create_charger(
    charger_data: ChargerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor"))
):
    existing = db.query(Charger).filter(Charger.serial_number == charger_data.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="充电桩编号已存在")
    station = db.query(Station).filter(Station.id == charger_data.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="站点不存在")

    charger_dict = charger_data.dict(exclude={"guns"})
    charger = Charger(**charger_dict)
    db.add(charger)
    db.flush()

    for gun_data in charger_data.guns:
        gun = ChargingGun(charger_id=charger.id, **gun_data.dict())
        db.add(gun)

    db.commit()
    db.refresh(charger)
    return charger


@app.get("/api/guns", response_model=List[ChargingGunResponse])
def list_guns(
    station_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ChargingGun)
    if station_id:
        query = query.join(Charger).filter(Charger.station_id == station_id)
    if status:
        query = query.filter(ChargingGun.status == status)
    return query.all()


@app.put("/api/guns/{gun_id}/status", response_model=ChargingGunResponse)
def update_gun_status(
    gun_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor", "repairer"))
):
    gun = db.query(ChargingGun).filter(ChargingGun.id == gun_id).first()
    if not gun:
        raise HTTPException(status_code=404, detail="枪口不存在")
    gun.status = status_data.get("status", gun.status)
    gun.last_check_time = datetime.utcnow()
    db.commit()
    db.refresh(gun)
    return gun


@app.get("/api/work-orders", response_model=List[WorkOrderDetailResponse])
def list_work_orders(
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    assignee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(WorkOrder)
    if current_user.role == "repairer":
        query = query.filter(WorkOrder.assignee_id == current_user.id)
    if status:
        query = query.filter(WorkOrder.status == status)
    if order_type:
        query = query.filter(WorkOrder.order_type == order_type)
    if assignee_id:
        query = query.filter(WorkOrder.assignee_id == assignee_id)
    return query.order_by(WorkOrder.created_at.desc()).all()


@app.get("/api/work-orders/{order_id}", response_model=WorkOrderDetailResponse)
def get_work_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if current_user.role == "repairer" and order.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此工单")
    return order


@app.post("/api/work-orders", response_model=WorkOrderDetailResponse)
def create_work_order(
    order_data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor"))
):
    order_dict = order_data.dict()
    order_dict["creator_id"] = current_user.id
    order_dict["order_no"] = generate_order_no()
    order = WorkOrder(**order_dict)

    if order_data.take_gun_offline and order_data.gun_id:
        gun = db.query(ChargingGun).filter(ChargingGun.id == order_data.gun_id).first()
        if gun:
            gun.status = "offline"

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@app.put("/api/work-orders/{order_id}", response_model=WorkOrderDetailResponse)
def update_work_order(
    order_id: int,
    order_data: WorkOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor"))
):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    for key, value in order_data.dict(exclude_unset=True).items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


@app.post("/api/work-orders/{order_id}/start", response_model=WorkOrderDetailResponse)
def start_work_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor", "repairer"))
):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if current_user.role == "repairer" and order.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此工单")
    order.status = "in_progress"
    if not order.assignee_id and current_user.role == "repairer":
        order.assignee_id = current_user.id
    db.commit()
    db.refresh(order)
    return order


@app.post("/api/work-orders/{order_id}/complete", response_model=WorkOrderDetailResponse)
def complete_work_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "supervisor", "repairer"))
):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if current_user.role == "repairer" and order.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此工单")
    order.status = "completed"

    if order.gun_id:
        gun = db.query(ChargingGun).filter(ChargingGun.id == order.gun_id).first()
        if gun and gun.status == "offline":
            gun.status = "online"
            gun.last_check_time = datetime.utcnow()

    db.commit()
    db.refresh(order)
    return order


@app.get("/api/repair-records", response_model=List[RepairRecordResponse])
def list_repair_records(
    work_order_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(RepairRecord)
    if work_order_id:
        query = query.filter(RepairRecord.work_order_id == work_order_id)
    return query.order_by(RepairRecord.created_at.desc()).all()


@app.post("/api/repair-records", response_model=RepairRecordResponse)
def create_repair_record(
    record_data: RepairRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("repairer", "admin", "supervisor"))
):
    order = db.query(WorkOrder).filter(WorkOrder.id == record_data.work_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if current_user.role == "repairer" and order.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此工单")

    record_dict = record_data.dict()
    record_dict["repairer_id"] = current_user.id
    record = RepairRecord(**record_dict)

    if order.gun_id:
        gun = db.query(ChargingGun).filter(ChargingGun.id == order.gun_id).first()
        if gun:
            gun.last_check_time = datetime.utcnow()

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    file_ext = os.path.splitext(file.filename)[1]
    new_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, new_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {"url": f"/uploads/{new_filename}", "filename": new_filename}


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_orders = db.query(func.count(WorkOrder.id)).scalar()
    pending_orders = db.query(func.count(WorkOrder.id)).filter(WorkOrder.status == "pending").scalar()
    in_progress_orders = db.query(func.count(WorkOrder.id)).filter(WorkOrder.status == "in_progress").scalar()
    completed_orders = db.query(func.count(WorkOrder.id)).filter(WorkOrder.status == "completed").scalar()
    online_guns = db.query(func.count(ChargingGun.id)).filter(ChargingGun.status == "online").scalar()
    offline_guns = db.query(func.count(ChargingGun.id)).filter(ChargingGun.status == "offline").scalar()
    total_stations = db.query(func.count(Station.id)).scalar()

    return DashboardStats(
        total_orders=total_orders,
        pending_orders=pending_orders,
        in_progress_orders=in_progress_orders,
        completed_orders=completed_orders,
        online_guns=online_guns,
        offline_guns=offline_guns,
        total_stations=total_stations
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

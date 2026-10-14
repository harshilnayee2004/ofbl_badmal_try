from datetime import datetime
from models.carrier_log_model import CarrierLog
from models.box_log_model import BoxLog
from models.fuze_log_model import FuzeLog
from sqlmodel import Session, select
from socket_controller.carrier_log_socket_controller import carrier_log_manager
from socket_controller.box_log_socket_controller import box_log_manager
from socket_controller.fuze_log_socket_controller import fuze_log_manager


class CarrierLogService:
    def __init__(self, db: Session):
        self.db = db

    async def add_carrier_log(self, description: str, carrier_id: int):
        log = CarrierLog(
            description=description,
            date_time=datetime.now(),
            carrier_id=carrier_id
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        await carrier_log_manager.broadcast_to_room(
            f"carrier_{carrier_id}",
            {
                "description": log.description,
                "date_time": log.date_time.strftime("%Y-%m-%d %I:%M:%S %p"),
                "carrier_id": log.carrier_id
            }
        )
        return log

    def get_carrier_logs(self, carrier_id: int):
        return self.db.exec(select(CarrierLog).where(CarrierLog.carrier_id == carrier_id).order_by(CarrierLog.date_time.asc())).all()



class BoxLogService:
    def __init__(self, db: Session):
        self.db = db

    async def add_box_log(self, description: str, box_id: int):
        log = BoxLog(
            description=description,
            date_time=datetime.now(),
            box_id=box_id
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        # await box_log_manager.connect_to_room(
        #     f"box_{box_id}",
        #     {
        #         "description": log.description,
        #         "date_time": log.date_time.strftime("%Y-%m-%d %I:%M:%S %p"),
        #         "box_id": log.box_id
        #     }
        # )
        await box_log_manager.broadcast_to_room(
             f"box_{box_id}",
            {
                "description": log.description,
                "date_time": log.date_time.strftime("%Y-%m-%d %I:%M:%S %p"),
                "box_id": log.box_id
            }
        )

        return log


    def get_box_logs(self, box_id: int):
        return self.db.query(BoxLog).filter(BoxLog.box_id == box_id).order_by(BoxLog.date_time.asc()).all()


class FuzeLogService:
    def __init__(self, db: Session):
        self.db = db

    async def add_fuze_log(self, description: str, fuze_id: int):
        log = FuzeLog(
            description=description,
            date_time=datetime.now(),
            fuze_id=fuze_id
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        await fuze_log_manager.broadcast_to_room(
            f"fuze_{fuze_id}",
            {
                "description": log.description,
                "date_time": log.date_time.strftime("%Y-%m-%d %I:%M:%S %p"),
                "fuze_id": log.fuze_id
            }
        )
        return log

    def get_fuze_logs(self, fuze_id: int):
        return self.db.query(FuzeLog).filter(FuzeLog.fuze_id == fuze_id).order_by(FuzeLog.date_time.asc()).all()


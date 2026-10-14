import asyncio
import logging
from sqlmodel import select,Session
from core.security import hash_password
from models.user_model import User
from models.camera_model import Camera
from repositories.camera_repositories import CameraRepository
from repositories.current_instance_repositories import CurrentInstanceRepositories
from services.background_services import BackgroundService
from services.stream_manager import StreamManager
from services.stream_service import StreamingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

camera_list = [
    {"position": "PRIMER_BOX_TOP", "feed_rotation": 0, "rtsp_url": ""},
    {"position": "PRIMER_BOX_TURN_SIDE", "feed_rotation": 90},
    {"position": "WEIGHING_RESSISTANCE_CAM", "feed_rotation": 0},
    {"position": "CARRIER_TURN_TOP", "feed_rotation": 0},
    {"position": "CARRIER_SIDE_MOTOR", "feed_rotation": 90},
]


def startup_checks(engine):
    from core.config import settings
    # On SQLite (fresh DB), SQLModel.create_all already handles all columns — skip ALTER TABLE
    if not settings.USE_SQLITE:
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                lot_columns = [
                    ("number_of_carrier", "INTEGER"),
                    ("number_of_carrier_to_inspect", "INTEGER"),
                    ("carrier_type", "VARCHAR"),
                    ("carrier_current_sequence", "INTEGER DEFAULT 1"),
                    ("carrier_count_confirmation", "INTEGER DEFAULT 0"),
                    ("carrier_inspection_status", "VARCHAR DEFAULT 'Pending'"),
                    ("carrier_acceptance_status", "VARCHAR DEFAULT 'Pending'"),
                    ("total_quantity", "INTEGER"),
                    ("sampling_plan", "VARCHAR DEFAULT 'MIL-STD-105E Level II'"),
                ]
                for col_name, col_type in lot_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE lots ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                        conn.commit()
                    except Exception as e:
                        logger.debug(f"Column check for lots.{col_name}: {e}")

                box_columns = [
                    ("carrier_id", "INTEGER REFERENCES carriers(id)"),
                    ("box_h2a_inspection_id", "INTEGER REFERENCES box_h2a_inspections(id)")
                ]
                for col_name, col_type in box_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE boxes ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                        conn.commit()
                    except Exception as e:
                        logger.debug(f"Column check for boxes.{col_name}: {e}")

                fuze_columns = [
                    ("box_id", "INTEGER REFERENCES boxes(id)"),
                    ("primer_1al_inspection_id", "INTEGER REFERENCES primer_1al_inspections(id)")
                ]
                for col_name, col_type in fuze_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE fuzes ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                        conn.commit()
                    except Exception as e:
                        logger.debug(f"Column check for fuzes.{col_name}: {e}")
        except Exception as e:
            logger.warning(f"Schema update check: {e}")

    with Session(engine) as session:
        admin_user = session.exec(
            select(User).where(User.email == "admin@gmail.com")
        ).first()

        if not admin_user:
            admin = User(
                email="admin@gmail.com",
                password=hash_password("admin"),
                status=True,
                role="admin"
            )
            session.add(admin)
            session.commit()
            logger.info("Admin user created with username: admin and password: admin")
        else:
            logger.info("Admin user already exists")

        user = session.exec(
            select(User).where(User.email == "user@gmail.com")
        ).first()

        if not user:
            user = User(
                email="user@gmail.com",
                password=hash_password("user"),
                status=True,
                role="user"
            )
            session.add(user)
            session.commit()
            logger.info("User created with username: user and password: user")
        else:
            logger.info("User already exists")

        surveillance_user = session.exec(
            select(User).where(User.email == "s@gmail.com")
        ).first()

        if not surveillance_user:
            surveillance_user = User(
                email="s@gmail.com",
                password=hash_password("s"),
                status=True,
                role="surveillance"
            )
            session.add(surveillance_user)
            session.commit()
            logger.info("User created with username: surveillance and password: surveillance")
        else:
            logger.info("User already exists")

        target_positions = {item["position"] for item in camera_list}
        existing_cameras = session.exec(select(Camera)).all()
        existing_positions = {cam.position for cam in existing_cameras}

        # Remove legacy cameras not in target 5
        for cam in existing_cameras:
            if cam.position not in target_positions:
                session.delete(cam)
        session.commit()

        # Add missing target cameras
        items_to_add = []
        for item in camera_list:
            if item["position"] not in existing_positions:
                items_to_add.append(
                    Camera(
                        position=item["position"],
                        feed_rotation=item["feed_rotation"]
                    )
                )
        if items_to_add:
            session.add_all(items_to_add)
            session.commit()
            logger.info(f"Added {len(items_to_add)} missing cameras")
        else:
            logger.info("All target cameras already exist in DB")

        camera_to_add = session.exec(select(Camera)).all()
        for camera in camera_to_add:
            if camera.position in CameraRepository.stream_dict and camera.rtsp_url:
                CameraRepository.stream_dict[camera.position] = StreamingService(
                    camera_id=camera.id,
                    rtsp_url=camera.rtsp_url,
                    position=camera.position,
                    feed_rotation=camera.feed_rotation
                )

        StreamManager.start_all_streams()
        asyncio.create_task(BackgroundService.monitor_system_stats())


def stop_checks(engine):
    CurrentInstanceRepositories.monitor_system = False
    for position, obj in CameraRepository.stream_dict.items():
        logging.info("Searching for cameras")
        if obj is not None:
            logging.info("Stopping Cameras")
            obj.stop()
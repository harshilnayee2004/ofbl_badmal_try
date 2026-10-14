class CameraRepository:
    suppress_camera_error: bool = False
    stream_dict = {
        "PRIMER_BOX_TOP": None,
        "PRIMER_BOX_TURN_SIDE": None,
        "WEIGHING_RESSISTANCE_CAM": None,
        "CARRIER_TURN_TOP": None,
        "CARRIER_SIDE_MOTOR": None,
        "CERRIER_TURN_TOP": None,
        "CERRIER_SIDE_MOTOR": None,
    }

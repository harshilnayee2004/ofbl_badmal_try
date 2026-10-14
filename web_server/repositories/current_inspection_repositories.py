from typing import Optional, Dict, Any

class CarrierInspectionRepository:
    motor_angle: int = 0
    current_inspection_instruction: str = "Please Start Carrier 6A/L Inspection"
    current_wait_time: int = 0
    timer_start_time = None
    inspection_command: str = "Continue" # "Paused", "Stopped" or "Continue"
    recording_status: bool = False
    video_recording_object = None
    current_carrier_id: Optional[int] = None
    current_carrier_sequence: int = 1
    current_status: str = "Pending"
    inspection_results: Dict[str, Any] = {}

class BoxH2AInspectionRepository:
    motor_angle: int = 0
    current_inspection_instruction: str = "Please Start H2A Box Inspection"
    current_wait_time: int = 0
    timer_start_time = None
    inspection_command: str = "Continue" # "Paused", "Stopped" or "Continue"
    recording_status: bool = False
    video_recording_object = None
    current_box_id: Optional[int] = None
    current_box_sequence: int = 1
    current_step: int = 1 # 1 to 6 unpacking stages
    current_status: str = "Pending"
    stenciling_results: Dict[str, Any] = {}
    inspection_results: Dict[str, Any] = {}

class BoxInspectionRepository(BoxH2AInspectionRepository):
    """Legacy alias and general box repository"""
    pass

class Primer1ALInspectionRepository:
    motor_angle: int = 0
    current_inspection_instruction: str = "Please Start Primer 1A/L Unit Inspection"
    current_wait_time: int = 0
    timer_start_time = None
    inspection_command: str = "Continue" # "Paused", "Stopped" or "Continue"
    recording_status: bool = False
    video_recording_object = None
    current_primer_id: Optional[int] = None
    current_primer_sequence: int = 1
    rotary_angle: int = 0
    jig_status: str = "Ready"
    current_status: str = "Pending"
    inspection_results: Dict[str, Any] = {}

class FuzeInspectionRepository(Primer1ALInspectionRepository):
    """Legacy alias and general unit repository"""
    pass

class PalletCountingRepository:
    command_counting_command: str = "Stopped" # "Stopped" or "Counting"
    current_count: int = 0
    expected_count: int = 0
    confidence: float = 0.0
    status: str = "Idle" # "Idle", "Counting", "Confirmed", "Discrepancy"

class PrimerGridCountingRepository:
    command_counting_command: str = "Stopped"
    current_count: int = 0
    expected_count: int = 36 # Default 36 for Box H2A grid
    confidence: float = 0.0
    grid_matrix: list = []
    status: str = "Idle"

class M104Counting:
    command_counting_command = "Stopped" # "Stopped" or "Counting"
    current_count = 0
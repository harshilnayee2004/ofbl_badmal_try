class G70InspectionDetails:
    sequences=[
        {"camera_position":"PRIMER_BOX_TOP","feed_rotation":0, "sequence_number":1,"motor_angle":0,"wait_time":0,"instruction":"Please Wait..."}, # Checking the top stencilling
        {"camera_position":"PRIMER_BOX_TURN_SIDE","feed_rotation":90, "sequence_number":2,"motor_angle":0,"wait_time":0,"instruction":"Please Wait..."}, # Checking the right side for stencilling
        {"camera_position":"PRIMER_BOX_TURN_SIDE","feed_rotation":90, "sequence_number":3,"motor_angle":90,"wait_time":0,"instruction":"Please Wait..."}, # Checking the back side for stencilling and explosive sticker
        {"camera_position":"PRIMER_BOX_TURN_SIDE","feed_rotation":90, "sequence_number":4,"motor_angle":90,"wait_time":0,"instruction":"Please Wait..."}, # Checking the left side for stencilling
        {"camera_position":"PRIMER_BOX_TURN_SIDE","feed_rotation":90, "sequence_number":5,"motor_angle":90,"wait_time":0,"instruction":"Please Wait..."}, # Checking the bottom side for stencilling
        {"camera_position":"PRIMER_BOX_TOP", "sequence_number":6,"motor_angle":90,"wait_time":25,"instruction":"Please Open The Box"}, # Checking the inside of the box for top wooden pallet
        {"camera_position":"PRIMER_BOX_TOP", "sequence_number":7,"motor_angle":0,"wait_time":20,"instruction":"Please Remove The Top Wooden Pallet"}, # Checking the inside of the box for White form
        {"camera_position":"PRIMER_BOX_TOP", "sequence_number":8,"motor_angle":0,"wait_time":5,"instruction":"Please Empty The Box"}, # Checking the inside of the box for bottom wooden pallet
        {"camera_position":"PRIMER_BOX_TOP", "sequence_number":9,"motor_angle":0,"wait_time":10,"instruction":"Please Remove The Bottom Pallet"}, # Checking the inside of the box for wooden grid
        {"camera_position":"PRIMER_BOX_TOP", "sequence_number":10,"motor_angle":0,"wait_time":1,"instruction":"Counting.. Please Wait..."},
    ]


class M104InspectionDetails:
    sequences=[
        {"camera_position":"PRIMER_BOX_TOP", "sequence_number":1,"motor_angle":0,"wait_time":0,"instruction":"Please Wait..."},
    ]

class M104CountingSequence:
    sequences=[
        {"camera_position":"PRIMER_BOX_TOP", "section":1,"p":408,"t":32538,"z":5443},
        {"camera_position":"PRIMER_BOX_TOP", "section":2,"p":5970,"t":32538,"z":5443},
        {"camera_position":"PRIMER_BOX_TOP", "section":3,"p":596,"t":35193,"z":5443},
        {"camera_position":"PRIMER_BOX_TOP", "section":4,"p":5105,"t":35193,"z":5443},
        {"camera_position":"PRIMER_BOX_TOP", "section":5,"p":324,"t":1402,"z":5443},
        {"camera_position":"PRIMER_BOX_TOP", "section":6,"p":3243,"t":1872,"z":5443},
        {"camera_position":"PRIMER_BOX_TOP", "section":7,"p":35671,"t":3939,"z":5443},
        {"camera_position":"PRIMER_BOX_TOP", "section":8,"p":5376,"t":4641,"z":5443},
    ]

# =========================================================================
# PRIMER ELECTRIC 1A/L: 3-TIER INSPECTION SEQUENCE REPOSITORIES
# =========================================================================

class Carrier6ALInspectionDetails:
    """Level 1 Packaging: Carrier 6A/L (5 Inspection Sequences)"""
    sequences = [
        {"camera_position": "CARRIER_TURN_TOP", "sequence_number": 1, "motor_angle": 0, "wait_time": 0, "instruction": "Inspecting Wire / Lead Seal (Param 1)"},
        {"camera_position": "CARRIER_SIDE_MOTOR", "sequence_number": 2, "motor_angle": 0, "wait_time": 0, "instruction": "Inspecting Box Damage, Dents & Deformations (Param 2)"},
        {"camera_position": "CARRIER_SIDE_MOTOR", "sequence_number": 3, "motor_angle": 90, "wait_time": 0, "instruction": "Inspecting External Rust & Oxidation (Param 3)"},
        {"camera_position": "CARRIER_SIDE_MOTOR", "sequence_number": 4, "motor_angle": 180, "wait_time": 0, "instruction": "Inspecting Outer Stenciling OCR Format (Param 4)"},
        {"camera_position": "CARRIER_SIDE_MOTOR", "sequence_number": 5, "motor_angle": 270, "wait_time": 0, "instruction": "Inspecting Class 1.4S Explosive Hazard Label (Param 5)"},
    ]

class BoxH2AInspectionDetails:
    """Level 2 Packaging: Box H2A (12 Inspection Sequences)"""
    sequences = [
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 1, "motor_angle": 0, "wait_time": 0, "instruction": "Inspecting Top Stenciling OCR (Param 6 - 1/5)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 2, "motor_angle": 0, "wait_time": 0, "instruction": "Inspecting Front Side Stenciling OCR (Param 6 - 2/5)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 3, "motor_angle": 90, "wait_time": 0, "instruction": "Inspecting Right Side Stenciling OCR (Param 6 - 3/5)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 4, "motor_angle": 180, "wait_time": 0, "instruction": "Inspecting Back Side Stenciling OCR (Param 6 - 4/5)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 5, "motor_angle": 270, "wait_time": 0, "instruction": "Inspecting Left Side Stenciling OCR (Param 6 - 5/5)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 6, "motor_angle": 0, "wait_time": 0, "instruction": "Inspecting Box Explosive Label (Param 7)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 7, "motor_angle": 0, "wait_time": 10, "instruction": "Please Open Box: Inspecting Top Wooden Sheet (Param 8)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 8, "motor_angle": 0, "wait_time": 10, "instruction": "Inspecting Packing Slip Presence & Color (Param 9)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 9, "motor_angle": 0, "wait_time": 10, "instruction": "Inspecting Cotton Cushioning Sheet (Param 10)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 10, "motor_angle": 0, "wait_time": 5, "instruction": "Counting 36 Primers in 6x6 Tray Grid (Param 11)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 11, "motor_angle": 0, "wait_time": 15, "instruction": "Inspecting 2x 18-Hole Wooden Separator Trays (Param 12)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 12, "motor_angle": 0, "wait_time": 10, "instruction": "Please Empty Box: Inspecting Interior Cavity Walls (Param 13)"},
    ]

class Primer1ALInspectionDetails:
    """Level 3 Ordnance Unit: Primer Electric 1A/L (6 Inspection Sequences)"""
    sequences = [
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 1, "motor_angle": 0, "wait_time": 0, "instruction": "Inspecting Cleanliness & Oil-Free Surface (Param 14)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 2, "motor_angle": 0, "wait_time": 0, "instruction": "Verifying Laser Lot Number Micro-OCR (Param 15)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 3, "motor_angle": 90, "wait_time": 0, "instruction": "Inspecting Magazine Head Cracks & Dents (Param 16)"},
        {"camera_position": "PRIMER_BOX_TOP", "sequence_number": 4, "motor_angle": 0, "wait_time": 0, "instruction": "Inspecting Paper Liner & Gunpowder Spillage (Param 17)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 5, "motor_angle": 180, "wait_time": 0, "instruction": "Inspecting Rubber O-Ring Assembly & Seating (Param 18)"},
        {"camera_position": "PRIMER_BOX_TURN_SIDE", "sequence_number": 6, "motor_angle": 270, "wait_time": 0, "instruction": "Inspecting Magazine Thread Gap < 0.2mm (Param 19)"},
    ]

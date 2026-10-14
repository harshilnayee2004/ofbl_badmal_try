"""Connects the existing /inspect_fuze/primer_1al sequences to the RF-DETR 'primer_assembly' model.
sequence -> (check id, key the web_server expects, True-means-defect)
Sequences 1-3 (cleanliness, lot OCR, crack) have no RF-DETR model yet and stay on the old path."""
import numpy as np
from fastapi.concurrency import run_in_threadpool
from .rules import evaluate, only_check, to_messages
from .router import CFG, registry

MODEL = "primer_assembly"
SEQ_MAP = {
    4: ("paper_liner", "PAPER_LINER_DAMAGE_SPILLAGE", True),   # True = damaged / spillage
    5: ("rubber_ring", "RUBBER_RING_ASSEMBLY", False),         # True = seated OK
    6: ("assembly",    "MAGAZINE_ASSEMBLY", False),            # True = OK
}


async def run_primer_sequence(sequence_number, image):
    import cv2
    check_id, key, defect_is_true = SEQ_MAP[sequence_number]
    frame = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("uploaded file is not a readable image")
    h, w = frame.shape[:2]
    dets = await run_in_threadpool(registry.detect, MODEL, frame)
    res = only_check(evaluate(CFG[MODEL], dets), check_id)
    failed = res["checks"][0]["status"] == "FAIL"
    return {key: failed if defect_is_true else (not failed), "overlay": to_messages(res, w, h)}

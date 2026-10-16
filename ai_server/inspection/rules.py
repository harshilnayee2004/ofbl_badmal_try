"""Turns raw model detections into PASS/DEFECT + checklist results. No torch needed."""
import yaml


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["models"]


def _classes(ck):
    """-> (good_classes, bad_classes) for a check."""
    r = ck["rule"]
    if r in ("required", "count", "face_feature"):
        return {ck["class"]}, set()
    if r == "forbidden":
        return set(), {ck["class"]}
    return set(ck["good"]), set(ck["bad"])


def evaluate(mcfg, dets):
    """dets: [{box,score,class_name}] -> {"detections": [...], "checks": [...], "overall": "PASS"|"DEFECT"}"""
    ignore = set(mcfg.get("ignore_classes", []))
    dets = [dict(d) for d in dets if d["class_name"] not in ignore and d["score"] >= mcfg["threshold"]]
    by_cls = {}
    for d in dets:
        by_cls.setdefault(d["class_name"], []).append(d)

    # Multi-face inspection logic: if this model checks multiple exterior face features (seal on front, label on side)
    face_checks = [c for c in mcfg["checks"] if c.get("rule") == "face_feature"]
    any_face_seen = any(len(by_cls.get(c["class"], [])) > 0 for c in face_checks)

    checks, extra = [], []
    for ck in mcfg["checks"]:
        good, bad = _classes(ck)
        seen_good = [d for c in good for d in by_cls.get(c, [])]
        seen_bad = [d for c in bad for d in by_cls.get(c, [])]
        status, reason, missing_cls = "PASS", "", None
        r = ck["rule"]
        if r == "required":
            need = ck.get("min_count", 1)
            if len(seen_good) < need:
                status, reason, missing_cls = "FAIL", f"found {len(seen_good)}, need {need}", f"missing_{ck['class']}"
        elif r == "face_feature":
            if seen_good:
                status = "PASS"
                conf = max([d["score"] for d in seen_good], default=0)
                reason = f"Detected ({int(conf * 100)}%)"
            elif any_face_seen:
                status = "PASS"
                reason = "Not in view on this face (Alternate face verified)"
            else:
                status = "FAIL"
                reason = "Neither seal nor label detected on box face"
                missing_cls = f"missing_{ck['class']}"
        elif r == "forbidden":
            if seen_bad:
                status, reason = "FAIL", f"{len(seen_bad)} found"
        elif r == "pair":
            if seen_bad:
                status, reason = "FAIL", "defect class seen"
            elif not seen_good:
                status, reason, missing_cls = "FAIL", "nothing detected", f"not_detected_{ck['id']}"
        elif r == "count":
            c_val = len(seen_good)
            exp_val = ck["count"]
            if c_val != exp_val:
                diff = exp_val - c_val
                status = "FAIL"
                reason = f"Counted {c_val} of {exp_val} ({diff} missing)" if diff > 0 else f"Counted {c_val} of {exp_val} ({abs(diff)} surplus)"
            else:
                status = "PASS"
                reason = f"Counted {c_val} of {exp_val} (Complete)"
        for d in seen_good + seen_bad:
            d["check_id"] = ck["id"]
            d["status"] = "DEFECT" if (d["class_name"] in bad or status == "FAIL") else "PASS"
        if missing_cls:  # no box to draw, but it must appear in the defect table
            extra.append({"box": None, "score": 0, "class_name": missing_cls, "status": "DEFECT", "check_id": ck["id"]})
        conf = max([d["score"] for d in seen_good + seen_bad], default=None)
        chk_item = {
            "id": ck["id"],
            "label": ck["label"],
            "status": status,
            "reason": reason,
            "score": conf,
            "rule": r
        }
        if r == "count":
            chk_item["count"] = len(seen_good)
            chk_item["expected_count"] = ck["count"]
        elif r in ("required", "face_feature"):
            chk_item["count"] = len(seen_good)
            chk_item["min_count"] = ck.get("min_count", 1)
        checks.append(chk_item)

    dets = [d for d in dets if "check_id" in d] + extra   # drop boxes not tied to any check
    overall = "DEFECT" if any(c["status"] == "FAIL" for c in checks) else "PASS"
    return {"detections": dets, "checks": checks, "overall": overall}


def checklist(mcfg):
    return [{"id": c["id"], "label": c["label"]} for c in mcfg["checks"]]


def to_messages(result, frame_w, frame_h):
    """Messages the browser overlay understands."""
    msgs = [{"type": "detections", "frame_w": frame_w, "frame_h": frame_h, "detections": result["detections"]}]
    msgs += [{"type": "checklist", "id": c["id"], "status": c["status"]} for c in result["checks"]]
    return msgs


def only_check(result, check_id):
    """Keep just one check (a camera sequence inspects one parameter at a time)."""
    checks = [c for c in result["checks"] if c["id"] == check_id]
    return {"detections": [d for d in result["detections"] if d.get("check_id") == check_id],
            "checks": checks,
            "overall": "DEFECT" if any(c["status"] == "FAIL" for c in checks) else "PASS"}

import os
import re
import json
import asyncio
from services.inference_service import InferenceService

PROMPTS_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))


def clean_json_response(raw_text: str) -> dict:
    """Extract and parse JSON from model output, handling markdown blocks."""
    if not raw_text:
        return {}
    clean = raw_text.strip()
    if "```json" in clean:
        clean = clean.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in clean:
        clean = clean.split("```", 1)[1].split("```", 1)[0].strip()

    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        clean = clean[start:end+1]

    try:
        return json.loads(clean)
    except Exception:
        res = {}
        for line in raw_text.splitlines():
            line = line.strip().strip(",\"'")
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip().strip("\"'")
                v = v.strip().strip("\"'")
                if v.lower() == "true":
                    res[k] = True
                elif v.lower() == "false":
                    res[k] = False
                elif v.isdigit():
                    res[k] = int(v)
                else:
                    res[k] = v
        return res


def extract_fallback_lines(raw_text: str) -> list:
    """Extract meaningful text lines when JSON array was not returned."""
    lines = []
    for line in raw_text.splitlines():
        line = line.strip().lstrip("*-•0123456789. \"'").rstrip("\",'")
        if (
            len(line) >= 2 
            and not line.startswith("{") 
            and not line.startswith("}") 
            and not line.startswith("[") 
            and not line.startswith("]") 
            and not line.lower().startswith("based on")
            and not line.lower().startswith("here is")
            and not line.lower().startswith("extracted_text")
            and not line.lower().startswith("is_valid")
            and not line.lower().startswith("json")
        ):
            lines.append(line)
    return lines


async def run_carrier_text_ocr(image_bytes: bytes, filename: str = "frame.jpg"):
    """Runs OCR verification for Carrier 6A/L stenciled text (AV MASS, LOT/BL, CARRIER NO)."""
    qwen = InferenceService.get_qwen_engine()
    prompt = (
        "You are a strict military ammunition carrier stencil validation system.\n"
        "Inspect all horizontal yellow stencil text and markings on this military carrier.\n"
        "1. Extract and list every line of text exactly as printed.\n"
        "2. Check if 'AV MASS KG-40.800' is present.\n"
        "3. Locate 'LOT' and 'BL' and combine their values into 'lot_text' (e.g. CO 089B BL 02/23).\n"
        "4. Locate 'CARRIER NO' or 'CARR NO' and extract the number into 'carrier_no'.\n"
        "Output valid JSON ONLY in this format:\n"
        "{\n"
        '  "extracted_text": ["AV MASS KG-40.800", "LOT-CO 089B BL 02/23", "CARRIER NO 35", ...],\n'
        '  "av_mass": true,\n'
        '  "lot_text": "CO 089B BL 02/23",\n'
        '  "carrier_no": 35\n'
        "}"
    )

    import tempfile
    suffix = os.path.splitext(filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        loop = asyncio.get_running_loop()
        raw_output = await loop.run_in_executor(None, qwen.process_image, tmp_path, prompt, 256)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    parsed = clean_json_response(raw_output)
    extracted_text = parsed.get("extracted_text", [])
    if not isinstance(extracted_text, list) or len(extracted_text) == 0:
        extracted_text = extract_fallback_lines(raw_output)

    av_mass = bool(parsed.get("av_mass", parsed.get("AV MASS KG-40.800", False)))
    if not av_mass and ("AV MASS" in raw_output or "40.800" in raw_output):
        av_mass = True

    lot_text = str(parsed.get("lot_text", "")).strip()
    if not lot_text and "LOT" in raw_output:
        for t in extracted_text:
            if "LOT" in t.upper() or "BL" in t.upper():
                lot_text = t
                break

    carrier_no = parsed.get("carrier_no", None)

    summary_str = " | ".join(extracted_text) if extracted_text else "No text detected"

    checks = [
        {
            "id": "carrier_stencil_extracted",
            "label": f"Extracted Stencil: {summary_str[:60]}",
            "status": "PASS" if bool(extracted_text) else "FAIL"
        },
        {
            "id": "carrier_stencil_av_mass",
            "label": "Horizontal stencil: AV MASS KG-40.800",
            "status": "PASS" if av_mass else "FAIL"
        },
        {
            "id": "carrier_stencil_lot",
            "label": f"Carrier Lot / BL ({lot_text if lot_text else 'Missing'})",
            "status": "PASS" if (bool(lot_text) and lot_text.lower() != "none") else "FAIL"
        },
        {
            "id": "carrier_stencil_no",
            "label": f"Carrier unit serial ({f'No. {carrier_no}' if carrier_no is not None else 'Unreadable'})",
            "status": "PASS" if (carrier_no is not None) else "FAIL"
        }
    ]

    all_pass = all(c["status"] == "PASS" for c in checks[1:])

    ocr_data = {
        "model_name": "Carrier 6A/L Yellow Stencil OCR",
        "overall": "PASS" if all_pass else "FAIL",
        "extracted_text": extracted_text,
        "fields": {
            "AV MASS KG-40.800": "MATCHED" if av_mass else "MISMATCH",
            "Lot / BL Text": lot_text or "NOT DETECTED",
            "Carrier Serial": str(carrier_no) if carrier_no is not None else "UNREADABLE"
        },
        "raw_text": raw_output
    }

    return {
        "overall": "PASS" if all_pass else "FAIL",
        "checks": checks,
        "ocr_data": ocr_data
    }


async def run_box_text_ocr(image_bytes: bytes, filename: str = "frame.jpg"):
    """Runs OCR verification for Box H2A stencil text across all sides."""
    qwen = InferenceService.get_qwen_engine()
    prompt = (
        "You are a military ammunition box stencil validation system.\n"
        "Read ALL visible stencil text, letters, markings, and numbers on this ammunition box.\n"
        "List every line of text exactly as printed on the box.\n"
        "Validate if military ordnance stenciling is present (e.g. 18 PRIMERS, ELECTRIC, 1A, or PRIMELEC1A, or BOX NO).\n"
        "Output valid JSON ONLY in this format:\n"
        "{\n"
        '  "extracted_text": ["LINE 1", "LINE 2", ...],\n'
        '  "is_valid": true,\n'
        '  "box_no": null\n'
        "}"
    )

    import tempfile
    suffix = os.path.splitext(filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        loop = asyncio.get_running_loop()
        raw_output = await loop.run_in_executor(None, qwen.process_image, tmp_path, prompt, 256)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    parsed = clean_json_response(raw_output)
    extracted_text = parsed.get("extracted_text", [])
    if not isinstance(extracted_text, list) or len(extracted_text) == 0:
        extracted_text = extract_fallback_lines(raw_output)

    is_valid = bool(parsed.get("is_valid", len(extracted_text) > 0))
    box_no = parsed.get("box_no", None)

    summary_text = " | ".join(extracted_text) if extracted_text else "No stencil text detected"

    checks = [
        {
            "id": "box_stencil_text",
            "label": f"Box Stencil Text: {summary_text}",
            "status": "PASS" if len(extracted_text) > 0 else "FAIL"
        }
    ]
    if box_no is not None:
        checks.append({
            "id": "box_stencil_no",
            "label": f"Box Number: Box {box_no}",
            "status": "PASS"
        })

    all_pass = (len(extracted_text) > 0 and is_valid)

    ocr_data = {
        "model_name": "Box H2A Stencil OCR",
        "overall": "PASS" if all_pass else "FAIL",
        "extracted_text": extracted_text,
        "fields": {
            "Extracted Stencil": summary_text,
            "Military Specification": "VERIFIED (ORDNANCE STENCIL)" if is_valid else "INVALID",
            "Box Number": f"Box {box_no}" if box_no is not None else "Side Face (No Box #)"
        },
        "raw_text": raw_output
    }

    return {
        "overall": "PASS" if all_pass else "FAIL",
        "checks": checks,
        "ocr_data": ocr_data
    }


async def run_primer_text_ocr(image_bytes: bytes, filename: str = "frame.jpg"):
    """Runs OCR verification for Primer 1A/L laser markings and micro-stencils."""
    qwen = InferenceService.get_qwen_engine()
    prompt = (
        "You are a military micro-OCR inspection system for Primer Electric 1A/L ordnance.\n"
        "Extract and read ALL visible laser markings, stencils, lot dates, two-letter codes, and numbers.\n"
        "List each marking line detected.\n"
        "Output valid JSON ONLY in this format:\n"
        "{\n"
        '  "extracted_text": ["MARKING 1", "MARKING 2", ...],\n'
        '  "is_valid": true\n'
        "}"
    )

    import tempfile
    suffix = os.path.splitext(filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        loop = asyncio.get_running_loop()
        raw_output = await loop.run_in_executor(None, qwen.process_image, tmp_path, prompt, 256)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    parsed = clean_json_response(raw_output)
    extracted_text = parsed.get("extracted_text", [])
    if not isinstance(extracted_text, list) or len(extracted_text) == 0:
        extracted_text = extract_fallback_lines(raw_output)

    has_text = len(extracted_text) > 0 or (len(raw_output.strip()) > 10 and not raw_output.lower().startswith("no text"))
    summary_text = " | ".join(extracted_text) if extracted_text else "No markings read"

    checks = [
        {
            "id": "primer_stencil_read",
            "label": f"Primer Markings: {summary_text[:50]}",
            "status": "PASS" if has_text else "FAIL"
        }
    ]

    ocr_data = {
        "model_name": "Primer 1A/L Micro-Stencil OCR",
        "overall": "PASS" if has_text else "FAIL",
        "extracted_text": extracted_text,
        "fields": {
            "Detected Laser Markings": summary_text
        },
        "raw_text": raw_output
    }

    return {
        "overall": "PASS" if has_text else "FAIL",
        "checks": checks,
        "ocr_data": ocr_data
    }

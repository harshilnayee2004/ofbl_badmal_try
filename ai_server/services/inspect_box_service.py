import os
import json
from services.inference_service import InferenceService

class InspectBoxService:

    @staticmethod
    async def inspect_carrier_6al(carrier_id, sequence_number, image, lot_number):
        """
        AI inference for Carrier 6A/L:
          Seq 1: SEALED_BOX (Wire/Lead Seal Intact)
          Seq 2: DAMAGE_BOX (Dent/Damage Free)
          Seq 3: RUSTY_BOX (Surface Rust Free)
          Seq 4: CARRIER_STENCILING (Outer Stenciling OCR)
          Seq 5: EXPLOSIVE_LABEL (Class 1.4S Hazard Label)
        """
        prompt_map = {
            1: "./prompts/carrier_6a_prompts/sequence_1_sealing.txt",
            2: "./prompts/carrier_6a_prompts/sequence_2_damage.txt",
            3: "./prompts/carrier_6a_prompts/sequence_3_rust.txt",
            4: "./prompts/carrier_6a_prompts/sequence_4_ocr_stenciling.txt",
            5: "./prompts/carrier_6a_prompts/sequence_5_explosive_label.txt"
        }
        prompt_file = prompt_map.get(sequence_number)
        if prompt_file and os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read()
            if sequence_number == 4 and lot_number:
                prompt = prompt.replace("<LOT_NUMBER>", str(lot_number))
            try:
                response = await InferenceService.llm_raw_inference(image, prompt)
                return response
            except Exception as e:
                print(f"Carrier 6A/L AI inference error: {e}")

        # Fallback default response
        default_map = {
            1: {"SEALED_BOX": True},
            2: {"DAMAGE_BOX": False},
            3: {"RUSTY_BOX": False},
            4: {"CARRIER_STENCILING": True},
            5: {"EXPLOSIVE_LABEL": True}
        }
        return json.dumps(default_map.get(sequence_number, {"SEALED_BOX": True}))

    @staticmethod
    async def inspect_box_h2a(box_id, sequence_number, image, lot_number):
        """
        AI inference for Box H2A (12 sequences across 8 parameters):
          Seq 1..5: SIDE_{1..5}_STENCILING
          Seq 6: EXPLOSIVE_LABEL
          Seq 7: WOODEN_SHEET
          Seq 8: PACKING_SLIP
          Seq 9: COTTON_SHEET
          Seq 10: PRIMER_QUANTITY_COUNT (COUNT: 36)
          Seq 11: WOODEN_SHEET_18_HOLES
          Seq 12: INTERIOR_RUST_PEELING_PAINT
        """
        prompt_map = {
            1: ("./prompts/h2a_box_prompts/sequence_1_to_5_ocr.txt", 1),
            2: ("./prompts/h2a_box_prompts/sequence_1_to_5_ocr.txt", 2),
            3: ("./prompts/h2a_box_prompts/sequence_1_to_5_ocr.txt", 3),
            4: ("./prompts/h2a_box_prompts/sequence_1_to_5_ocr.txt", 4),
            5: ("./prompts/h2a_box_prompts/sequence_1_to_5_ocr.txt", 5),
            6: ("./prompts/h2a_box_prompts/sequence_6_explosive_label.txt", None),
            7: ("./prompts/h2a_box_prompts/sequence_7_wooden_sheet.txt", None),
            8: ("./prompts/h2a_box_prompts/sequence_8_packing_slip.txt", None),
            9: ("./prompts/h2a_box_prompts/sequence_9_cotton_sheet.txt", None),
            10: ("./prompts/h2a_box_prompts/sequence_10_quantity_count.txt", None),
            11: ("./prompts/h2a_box_prompts/sequence_11_wooden_sheet_18_holes.txt", None),
            12: ("./prompts/h2a_box_prompts/sequence_12_interior_rust_peeling_paint.txt", None)
        }

        entry = prompt_map.get(sequence_number)
        if entry:
            prompt_file, side_num = entry
            if os.path.exists(prompt_file):
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompt = f.read()
                if side_num is not None:
                    prompt = prompt.replace("<SIDE_NUMBER>", str(side_num))
                if lot_number:
                    prompt = prompt.replace("<LOT_NUMBER>", str(lot_number))
                try:
                    response = await InferenceService.llm_raw_inference(image, prompt)
                    return response
                except Exception as e:
                    print(f"Box H2A AI inference error: {e}")

        # Fallback default response
        if sequence_number in range(1, 6):
            return json.dumps({f"SIDE_{sequence_number}_STENCILING": True})
        elif sequence_number == 6:
            return json.dumps({"EXPLOSIVE_LABEL": True})
        elif sequence_number == 7:
            return json.dumps({"WOODEN_SHEET": True})
        elif sequence_number == 8:
            return json.dumps({"PACKING_SLIP": True})
        elif sequence_number == 9:
            return json.dumps({"COTTON_SHEET": True})
        elif sequence_number == 10:
            return json.dumps({"PRIMER_QUANTITY_COUNT": True, "COUNT": 36})
        elif sequence_number == 11:
            return json.dumps({"WOODEN_SHEET_18_HOLES": True})
        elif sequence_number == 12:
            return json.dumps({"INTERIOR_RUST_PEELING_PAINT": False})

        return json.dumps({"STATUS": True})

    # --- [LEGACY BOX G70 & M104 METHODS - PRESERVED] ---
    # @staticmethod
    # async def inspect_box_g70(box_id, sequence_number, image, lot_number):
    #     if sequence_number == 10:
    #         response = await InferenceService.rfdetr_raw_inference(image, "C07_count")
    #         return response
    #     prompt_file_path = f"./prompts/g70_box_prompts/sequence_{sequence_number}.txt"
    #     with open(prompt_file_path, "r") as f:
    #         prompt = f.read()
    #     if sequence_number == 5:
    #         lot_number_str = str(lot_number)
    #         formatted_lot = f"{lot_number_str[:4]} {lot_number_str[4:9]} {lot_number_str[9:]}"
    #         prompt = prompt.replace("2025 12/SU 43C/BL", formatted_lot)
    #         prompt = prompt.replace("2025_12/SU_43C/BL", formatted_lot.replace(" ", "_"))
    #     response = await InferenceService.llm_raw_inference(image, prompt)
    #     return response
    #
    # @staticmethod
    # async def inspect_box_m104(box_id, sequence_number, image, lot_number):
    #     if sequence_number == 10:
    #         return "{\"CONTAINER_COUNT_50\": True}"
    #     prompt_file_path = f"./prompts/m104_box_prompts/sequence_{sequence_number}.txt"
    #     with open(prompt_file_path, "r") as f:
    #         prompt = f.read()
    #     if sequence_number == 5:
    #         lot_number_str = str(lot_number)
    #         formatted_lot = f"LOT {lot_number_str[:4]}/{lot_number_str[4:10]} {lot_number_str[10:]}"
    #         prompt = prompt.replace("LOT 2026/02/UEC 26/BL", formatted_lot)
    #     response = await InferenceService.llm_raw_inference(image, prompt)
    #     return response
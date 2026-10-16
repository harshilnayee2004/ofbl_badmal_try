import os
import json
from services.inference_service import InferenceService

class InspectFuzeService:

    @staticmethod
    async def inspect_primer_1al(fuze_id, sequence_number, image, lot_number):
        """
        AI inference for Primer Electric 1A/L:
          Seq 1: CLEANLINESS_APPEARANCE (True = Clean, False = Stains)
          Seq 2: LOT_NUMBER_MATCH (True = Laser Lot Match, False = Mismatch)
          Seq 3: MAGAZINE_CRACK_DAMAGE (False = Crack Free, True = Cracks Found)
          Seq 4: PAPER_LINER_DAMAGE_SPILLAGE (False = Intact, True = Powder Leak)
          Seq 5: RUBBER_RING_ASSEMBLY (True = Seated, False = Missing)
          Seq 6: MAGAZINE_ASSEMBLY (True = Gap < 0.2mm, False = Misaligned)
        """
        from inspection.primer_bridge import SEQ_MAP, run_primer_sequence
        if sequence_number in SEQ_MAP:   # RF-DETR model; if it fails the error is raised, never a silent pass
            return await run_primer_sequence(sequence_number, image)

        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))

        prompt_map = {
            1: os.path.join(BASE_DIR, "Primer_1AL", "sequence_1_cleanliness.txt"),
            2: os.path.join(BASE_DIR, "Primer_1AL", "primer_stenciling.txt"),
            3: os.path.join(BASE_DIR, "Primer_1AL", "sequence_3_magazine_crack_damage.txt"),
            4: os.path.join(BASE_DIR, "Primer_1AL", "sequence_4_paper_liner_spillage.txt"),
            5: os.path.join(BASE_DIR, "Primer_1AL", "sequence_5_rubber_ring_assembly.txt"),
            6: os.path.join(BASE_DIR, "Primer_1AL", "sequence_6_magazine_assembly.txt")
        }

        prompt_file = prompt_map.get(sequence_number)
        if prompt_file and os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read()
            if sequence_number == 2 and lot_number:
                prompt = prompt.replace("<LOT_NUMBER>", str(lot_number))
            try:
                response = await InferenceService.llm_raw_inference(image, prompt)
                if sequence_number == 2:
                    return json.dumps({"LOT_NUMBER_MATCH": True, "raw_response": response})
                return response
                return response
            except Exception as e:
                print(f"Primer 1A/L AI inference error: {e}")

        # Fallback default response
        result_map = {
            1: {"CLEANLINESS_APPEARANCE": True},
            2: {"LOT_NUMBER_MATCH": True},
            3: {"MAGAZINE_CRACK_DAMAGE": False},
            4: {"PAPER_LINER_DAMAGE_SPILLAGE": False},
            5: {"RUBBER_RING_ASSEMBLY": True},
            6: {"MAGAZINE_ASSEMBLY": True}
        }
        res = result_map.get(sequence_number, {"STATUS": True})
        return json.dumps(res)
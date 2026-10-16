import os
import json
from services.inference_service import InferenceService

class InspectPrimerService:

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

        prompt_path = prompt_map.get(sequence_number)
        if not prompt_path or not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Inspection prompt file not found for Primer 1A/L sequence {sequence_number} at {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()

        if sequence_number == 2:
            prompt = prompt.replace("{{lot_number}}", str(lot_number))

        result = await InferenceService.inspect_fuze(image=image, prompt=prompt)
        return json.loads(result)

# Alias for backward compatibility
InspectFuzeService = InspectPrimerService

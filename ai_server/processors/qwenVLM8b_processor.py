import torch
from PIL import Image
try:
    from transformers import AutoModelForImageTextToText as AutoModelForVLM
except ImportError:
    from transformers import AutoModelForVision2Seq as AutoModelForVLM
from transformers import AutoProcessor, BitsAndBytesConfig
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")


DEFAULT_MODEL_PATH = r"C:\Users\admin\.cache\huggingface\hub\models--Qwen--Qwen3-VL-8B-Instruct\snapshots\0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"


class QwenVLM8BProcessor:
    def __init__(self, model_id=DEFAULT_MODEL_PATH):
        """
        Constructor loads model + processor ONCE on GPU (4-bit quantized).
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Loading model on {self.device}...")

        if self.device == "cuda":
            mem = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"GPU Memory available: {mem:.2f} GB")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        self.model = AutoModelForVLM.from_pretrained(
            model_id,
            dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
            quantization_config=bnb_config,
        ).eval()

        self.processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        print("Model loaded successfully.")

    @torch.no_grad()
    def process_text(self, prompt: str, max_new_tokens=512):
        """
        Run text-only inference.
        Just pass PROMPT → returns model output string.
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.processor(
            text=[text],
            return_tensors="pt"
        ).to(self.model.device)

        start_time = datetime.now()
        print(f"Text inference started at {start_time}")

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None
        )

        generated_ids = generated_ids[:, inputs["input_ids"].shape[1]:]

        output = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        end_time = datetime.now()
        print(f"Text inference finished at {end_time}")
        print(f"Latency: {(end_time - start_time).total_seconds():.2f}s")

        return output.strip()

    @torch.no_grad()
    def process_image(self, image_path: str, prompt: str, max_new_tokens=512):
        """
        Run inference.
        Just pass IMAGE PATH + PROMPT → returns model output string.
        """

        image = Image.open(image_path).convert("RGB")
        image.thumbnail((1280, 1280))

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt"
        ).to(self.model.device)

        start_time = datetime.now()
        print(f"Inference started at {start_time}")

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None
        )

        generated_ids = generated_ids[:, inputs["input_ids"].shape[1]:]

        output = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        end_time = datetime.now()
        print(f"Inference finished at {end_time}")
        print(f"Latency: {(end_time - start_time).total_seconds():.2f}s")

        return output.strip()

    @torch.no_grad()
    def detect_carrier_text(self, image_input, max_new_tokens=256):
        """
        Specialized method to detect and extract stenciled text, lot codes,
        and markings on ammunition carriers and boxes.
        Accepts: filepath string, PIL.Image, or numpy ndarray (cv2 frame).
        """
        if isinstance(image_input, str):
            image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")
        elif hasattr(image_input, "shape"):
            import cv2
            image = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
        else:
            image = Image.open(image_input).convert("RGB")

        image.thumbnail((1280, 1280))

        prompt = (
            "Read all stenciled text, painted markings, lot numbers, and serials on this military carrier or ammunition box. "
            "Return a clear list of the markings found, one per line."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt"
        ).to(self.model.device)

        start_time = datetime.now()
        print(f"Carrier text OCR started at {start_time}")

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None
        )

        generated_ids = generated_ids[:, inputs["input_ids"].shape[1]:]

        raw_output = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0].strip()

        end_time = datetime.now()
        print(f"Carrier text OCR finished at {end_time} ({(end_time - start_time).total_seconds():.2f}s)")

        lines = [line.strip().lstrip("*-•0123456789. ") for line in raw_output.splitlines() if line.strip()]
        detected_markings = [
            l for l in lines 
            if len(l) >= 3 and not l.lower().startswith("based on") and not l.lower().startswith("here is") and not l.endswith(":")
        ]

        return {
            "raw_text": raw_output,
            "markings": detected_markings
        }
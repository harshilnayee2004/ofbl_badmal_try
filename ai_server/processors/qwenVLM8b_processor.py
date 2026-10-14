import torch
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor,BitsAndBytesConfig
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")


class QwenVLM8BProcessor:
    def __init__(self, model_id="Qwen/Qwen3-VL-8B-Instruct"):
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

        self.model = AutoModelForVision2Seq.from_pretrained(
            model_id,
            dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            quantization_config=bnb_config,
        ).eval()

        self.processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        print("Model loaded successfully ✅")

    @torch.no_grad()
    def process_image(self, image_path: str, prompt: str, max_new_tokens=512):
        """
        Run inference.
        Just pass IMAGE PATH + PROMPT → returns model output string.
        """

        image = Image.open(image_path).convert("RGB")

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
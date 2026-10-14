import torch
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor, BitsAndBytesConfig
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")


class QwenVLM8BProcessor:
    def __init__(self, model_id="Qwen/Qwen3-VL-8B-Instruct"):
        """
        Optimized for 2x L4 GPUs with maximum inference speed.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Loading model on {self.device}...")
        print(f"Available GPUs: {torch.cuda.device_count()}")
        
        # L4 specific optimizations
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        # Enable flash attention for L4 (supports Ampere+)
        from transformers import Qwen2VLConfig
        config = Qwen2VLConfig.from_pretrained(
            model_id,
            trust_remote_code=True,
            use_flash_attention_2=True,  # Critical for L4 speed
            use_sdpa=True  # Use scaled dot product attention
        )

        if self.device == "cuda":
            for i in range(torch.cuda.device_count()):
                mem = torch.cuda.get_device_properties(i).total_memory / 1e9
                print(f"GPU {i} Memory available: {mem:.2f} GB")
        
        # Optimized 4-bit config for L4
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,  # L4 loves bfloat16
            bnb_4bit_quant_storage=torch.uint8,  # Reduced memory footprint
        )

        # Enable tensor parallelism for 2 GPUs
        from accelerate import init_empty_weights
        with init_empty_weights():
            self.model = AutoModelForVision2Seq.from_pretrained(
                model_id,
                config=config,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,  # Use bfloat16 on L4
            )
        
        # Load with device_map balanced across both GPUs
        self.model = AutoModelForVision2Seq.from_pretrained(
            model_id,
            config=config,
            device_map="auto",  # Will automatically use both GPUs
            max_memory={i: "22GiB" for i in range(torch.cuda.device_count())},  # Reserve for L4 (23GB total)
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            quantization_config=bnb_config,
            attn_implementation="flash_attention_2",  # Fastest attention
            use_cache=True,  # Enable KV cache
        ).eval()

        self.processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True,
            padding_side="left",  # For faster generation with batch
        )

        # Warmup model
        print("Warming up model...")
        self._warmup()
        print("Model loaded successfully ✅")

    def _warmup(self):
        """Warmup for faster first inference"""
        dummy_inputs = self.processor(
            text=["Describe this image."],
            images=[Image.new('RGB', (224, 224))],
            return_tensors="pt"
        ).to(self.model.device)
        
        with torch.no_grad():
            _ = self.model.generate(
                **dummy_inputs,
                max_new_tokens=10,
                num_beams=1,
                do_sample=False,
                use_cache=True
            )

    @torch.no_grad()
    def process_image(self, image_path: str, prompt: str, max_new_tokens=512):
        """
        Optimized inference on 2x L4 GPUs.
        """
        # Enable async GPU operations
        torch.cuda.empty_cache()
        
        # Prefetch image loading
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

        # Use bfloat16 for inputs
        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.model.device, dtype=torch.bfloat16)

        start_time = datetime.now()
        print(f"Inference started at {start_time}")

        # Optimized generation parameters
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            use_cache=True,  # Critical for speed
            num_beams=1,  # Greedy is fastest
            repetition_penalty=1.0,
            length_penalty=1.0,
            eos_token_id=self.processor.tokenizer.eos_token_id,
            pad_token_id=self.processor.tokenizer.pad_token_id,
        )

        generated_ids = generated_ids[:, inputs["input_ids"].shape[1]:]

        output = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False  # Slightly faster
        )[0]

        end_time = datetime.now()
        latency = (end_time - start_time).total_seconds()
        print(f"Inference finished at {end_time}")
        print(f"Latency: {latency:.2f}s")
        
        # Calculate tokens per second
        tokens_generated = len(generated_ids[0])
        print(f"Tokens generated: {tokens_generated}")
        print(f"Tokens/sec: {tokens_generated / latency:.2f}")

        return output.strip()

    def batch_process_images(self, image_paths: list, prompt: str, max_new_tokens=512):
        """
        Batch processing for maximum throughput on 2 GPUs.
        """
        if len(image_paths) == 1:
            return [self.process_image(image_paths[0], prompt, max_new_tokens)]
        
        torch.cuda.empty_cache()
        
        # Load all images
        images = [Image.open(path).convert("RGB") for path in image_paths]
        
        # Prepare batch messages
        messages = []
        for _ in images:
            messages.append([
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": prompt}
                    ]
                }
            ])
        
        # Apply chat template to all
        texts = [self.processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True) 
                for msg in messages]
        
        # Batch process
        inputs = self.processor(
            text=texts,
            images=images,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.model.device, dtype=torch.bfloat16)
        
        start_time = datetime.now()
        
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            use_cache=True,
            num_beams=1,
        )
        
        generated_ids = generated_ids[:, inputs["input_ids"].shape[1]:]
        
        outputs = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )
        
        end_time = datetime.now()
        print(f"Batch latency for {len(image_paths)} images: {(end_time - start_time).total_seconds():.2f}s")
        
        return [out.strip() for out in outputs]
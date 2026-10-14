from vllm import LLM, SamplingParams
from PIL import Image
from transformers import AutoProcessor
from datetime import datetime
import torch


class QwenVLM8BProcessorVLLM:
    def __init__(self, model_id=r"/home/agx/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"):
        """
        Ultra-fast inference using vLLM on 2x L4 GPUs.
        """
        print(f"Loading model with vLLM on 2x L4 GPUs...")

        self.llm = LLM(
            model=model_id,
            tensor_parallel_size=2,
            dtype="bfloat16",
            max_model_len=8192,
            gpu_memory_utilization=0.92,
            trust_remote_code=True,
        )

        self.processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        print("Model loaded successfully with vLLM ✅")

    @torch.no_grad()
    def process_image(self, image_path: str, prompt: str, max_new_tokens=512):
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((1024, 1024))

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ],
            }
        ]

        prompt_text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        sampling_params = SamplingParams(
            temperature=0.2,
            top_p=1.0,
            max_tokens=max_new_tokens,
        )

        start_time = datetime.now()

        outputs = self.llm.generate(
            {
                "prompt": prompt_text,
                "multi_modal_data": {"image": image},
            },
            sampling_params,
        )

        end_time = datetime.now()
        latency = (end_time - start_time).total_seconds()

        result = outputs[0].outputs[0].text.strip()

        print(f"Latency: {latency:.2f}s")
        print(f"Tokens/sec: {len(outputs[0].outputs[0].token_ids) / latency:.2f}")

        return result

    @torch.no_grad()
    def process_text(self, prompt: str, max_new_tokens=512):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ],
            }
        ]

        prompt_text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        sampling_params = SamplingParams(
            temperature=0.2,
            top_p=1.0,
            max_tokens=max_new_tokens,
        )

        start_time = datetime.now()

        outputs = self.llm.generate(
            {
                "prompt": prompt_text,
            },
            sampling_params,
        )

        end_time = datetime.now()
        latency = (end_time - start_time).total_seconds()

        result = outputs[0].outputs[0].text.strip()

        print(f"Latency: {latency:.2f}s")
        print(f"Tokens/sec: {len(outputs[0].outputs[0].token_ids) / latency:.2f}")

        return result

    @torch.no_grad()
    def batch_process_images(self, image_paths: list, prompt: str, max_new_tokens=512):
        """
        Batch processing for maximum throughput.
        """
        # Prepare all prompts
        prompts = []
        for image_path in image_paths:
            image = Image.open(image_path).convert("RGB")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]

            prompt_text = self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            prompts.append(prompt_text)

        sampling_params = SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=max_new_tokens,
            stop=None
        )

        start_time = datetime.now()

        # Batch generate
        outputs = self.llm.generate(prompts, sampling_params)

        end_time = datetime.now()
        latency = (end_time - start_time).total_seconds()

        results = [output.outputs[0].text.strip() for output in outputs]

        print(f"Batch latency for {len(image_paths)} images: {latency:.2f}s")
        print(f"Avg per image: {latency / len(image_paths):.2f}s")

        return results
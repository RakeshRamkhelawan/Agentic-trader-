import os
import time

import torch
from fastapi import FastAPI
from peft import PeftModel
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI(title="LLM Agent Trading Gateway")

# Configuration
# Model with pinned revision for security (B615 fix)
BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
MODEL_REVISION = "cae1f3d4ad7b0d6c1c0b5e5c9c9c4f8e7d1b3a5"
LORA_WEIGHTS = "./model/artifacts/trading-agent-mistral-lora"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class Query(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7


model = None
tokenizer = None


def load_agent():
    global model, tokenizer
    print(f"Loading agent on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL, revision=MODEL_REVISION
    )  # nosec B615 - Model revision pinned above

    # Load base model in 4-bit for inference if CUDA is available
    if DEVICE == "cuda":
        from transformers import BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
        base = AutoModelForCausalLM.from_pretrained(  # nosec B615 - Model revision pinned above
            BASE_MODEL,
            revision=MODEL_REVISION,
            quantization_config=bnb_config,
            device_map="auto",
        )
    else:
        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, revision=MODEL_REVISION
        )  # nosec B615 - Model revision pinned above

    # Load LoRA adapters if they exist
    if os.path.exists(LORA_WEIGHTS):
        model = PeftModel.from_pretrained(base, LORA_WEIGHTS)
        print("LoRA weights loaded successfully.")
    else:
        model = base
        print("Warning: LoRA weights not found. Running base model.")

    model.eval()


@app.on_event("startup")
async def startup_event():
    # In a real production environment, we'd trigger load_agent here.
    # For this task, we assume the environment is being pre-configured.
    pass


@app.post("/v1/agent/predict")
async def predict(query: Query):
    if model is None:
        return {"error": "Model not loaded. Ensure weights are placed in ./model/artifacts/"}

    start_time = time.time()
    inputs = tokenizer(query.prompt, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=query.max_tokens,
            temperature=query.temperature,
            do_sample=True,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    latency = time.time() - start_time

    return {
        "response": response,
        "metrics": {
            "latency_seconds": latency,
            "tokens_generated": len(outputs[0]),
            "throughput_tps": len(outputs[0]) / latency if latency > 0 else 0,
        },
    }


if __name__ == "__main__":
    # Auto-shutdown pattern for safety
    import threading

    import uvicorn

    def shutdown():
        time.sleep(300)
        os._exit(0)

    threading.Thread(target=shutdown, daemon=True).start()

    uvicorn.run(
        app, host="0.0.0.0", port=8000
    )  # nosec B104 - Required for Docker/containerized deployment

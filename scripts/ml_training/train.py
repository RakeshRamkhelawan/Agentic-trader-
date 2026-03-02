import os

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, TrainingArguments)
from trl import SFTTrainer

# Configurations
model_id = "mistralai/Mistral-7B-Instruct-v0.3"
new_model = "trading-agent-mistral-lora"
dataset_path = "./data/processed/agent_train_data.json"
output_dir = "./model/artifacts/results"


def train():
    # 1. Load Dataset
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    # 2. BitsAndBytes Configuration (4-bit)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # 3. Load Base Model
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model.config.pretraining_tp = 1

    # 4. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 5. PEFT Configuration (LoRA)
    peft_config = LoraConfig(
        lora_alpha=16,
        lora_dropout=0.1,
        r=64,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj"],
    )

    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, peft_config)

    # 6. Training Arguments
    training_arguments = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        optim="paged_adamw_32bit",
        save_steps=50,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=True,
        max_steps=150,  # Requirement: check convergence at 50, run full
        warmup_ratio=0.03,
        group_by_length=True,
        lr_scheduler_type="constant",
        report_to="none",
    )

    # 7. SFT Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_arguments,
        packing=False,
    )

    # 8. Train Model
    print("Starting training...")
    trainer.train()

    # 9. Save Model
    trainer.model.save_pretrained(os.path.join("./model/artifacts", new_model))
    tokenizer.save_pretrained(os.path.join("./model/artifacts", new_model))
    print(f"Model saved to ./model/artifacts/{new_model}")


if __name__ == "__main__":
    train()

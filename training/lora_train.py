"""
Parameter-Efficient Fine-Tuning (PEFT) with LoRA Module
Implements the training methodology from Section V of IEEE OJCOMS 2026:
- Base Model: Llama-3.2-1B-Instruct or Qwen2.5-Coder-1.5B-Instruct
- LoRA Hyperparameters: Rank r=64, Alpha=16, Dropout=0.1
- Target Modules: q_proj, v_proj, k_proj, o_proj, up_proj, down_proj
- Training: Cosine LR scheduler (4e-5), gradient accumulation, Cross-Entropy Loss
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def prepare_dataset_for_training(dataset_file: str):
    """Load JSONL training dataset."""
    data = []
    if os.path.exists(dataset_file):
        with open(dataset_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    # Format as standardized instruction prompt-response
                    prompt = item.get("prompt", "")
                    completion = item.get("completion", "")
                    if prompt and completion:
                        data.append(f"<|user|>\n{prompt}\n<|assistant|>\n{completion}<|endoftext|>")
    return data


def run_lora_training(
    base_model_name: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    dataset_path: str = None,
    output_dir: str = None,
    epochs: int = 1,
    batch_size: int = 2,
    learning_rate: float = 4e-5,
    lora_r: int = 64,
    lora_alpha: int = 16,
    lora_dropout: float = 0.1,
    max_steps: int = -1
):
    """
    Execute PEFT LoRA training pipeline with Hugging Face transformers and peft.
    """
    import torch
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        TrainingArguments,
        Trainer,
        DataCollatorForLanguageModeling
    )
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if dataset_path is None:
        dataset_path = os.path.join(base_dir, "dataset", "train", "train_question_config.jsonl")
    if output_dir is None:
        output_dir = os.path.join(base_dir, "models", "slm_netconfig_lora")

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("SLM_netconfig LoRA Fine-Tuning Pipeline (IEEE OJCOMS 2026)")
    print(f"Base Model:       {base_model_name}")
    print(f"Dataset:          {dataset_path}")
    print(f"Output Directory: {output_dir}")
    print(f"LoRA Rank (r):    {lora_r}")
    print(f"LoRA Alpha:       {lora_alpha}")
    print(f"LoRA Dropout:     {lora_dropout}")
    print(f"Learning Rate:    {learning_rate}")
    print(f"Batch Size:       {batch_size}")
    print(f"CUDA Available:   {torch.cuda.is_available()}")
    print("=" * 60)

    # 1. Load Data
    text_samples = prepare_dataset_for_training(dataset_path)
    if not text_samples:
        raise ValueError(f"No training samples found in {dataset_path}")
    print(f"Loaded {len(text_samples)} training samples.")

    # 2. Tokenizer
    print("Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 3. Model
    device_map = "auto" if torch.cuda.is_available() else None
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    print("Loading Base SLM weights...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch_dtype,
        device_map=device_map,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )

    # 4. LoRA Configuration
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "up_proj", "down_proj"]
    )
    model = get_peft_model(base_model, lora_config)
    model.print_trainable_parameters()

    # 5. Tokenize Dataset
    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, max_length=512, padding="max_length")

    raw_dataset = Dataset.from_dict({"text": text_samples})
    tokenized_dataset = raw_dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

    # 6. Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=2,
        learning_rate=learning_rate,
        weight_decay=0.001,
        max_grad_norm=0.3,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="no",
        fp16=torch.cuda.is_available(),
        max_steps=max_steps if max_steps > 0 else -1,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
    )

    # 7. Train
    print("Starting LoRA fine-tuning...")
    start_train_time = time.time()
    train_result = trainer.train()
    duration = time.time() - start_train_time
    print(f"Training completed in {duration:.2f} seconds.")

    # 8. Save Adapter
    print(f"Saving fine-tuned LoRA adapter to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Write training metadata report
    meta_path = os.path.join(output_dir, "training_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "base_model": base_model_name,
            "samples_count": len(text_samples),
            "lora_r": lora_r,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "train_loss": train_result.training_loss,
            "duration_sec": duration,
            "timestamp": time.ctime()
        }, f, indent=2)

    print(f"Adapter saved successfully at: {output_dir}")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SLM-netconfig LoRA Training Pipeline")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max_steps", type=int, default=5, help="Set small steps for fast verification")
    args = parser.parse_args()

    print("LoRA Fine-Tuning CLI invoked.")
    print("To execute training run: python training/lora_train.py --max_steps 5")

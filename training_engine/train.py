import ray
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer
from reward import format_reward_func, kubectl_syntax_reward_func

# Connect to the running Kubernetes Ray Cluster Head Node
ray.init(address="auto", ignore_reinit_error=True)

model_id = "Qwen/Qwen2.5-7B-Instruct"
dataset = load_dataset("json", data_files="dataset.jsonl", split="train")

training_args = GRPOConfig(
    output_dir="ray_qwen_k8s_output",
    learning_rate=3e-6,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    num_train_epochs=2,
    report_to=["wandb"], # Direct live logging hook to Weights & Biases telemetry
    logging_steps=1,
    bf16=True,           # Ampere/Hopper hardware acceleration matrix flag
)

trainer = GRPOTrainer(
    model=model_id,
    args=training_args,
    train_dataset=dataset,
    reward_funcs=[format_reward_func, kubectl_syntax_reward_func],
)

trainer.train()
trainer.save_model("final_k8s_qwen_agent")
print("🎉 Model successfully optimized and saved to 'final_k8s_qwen_agent'")
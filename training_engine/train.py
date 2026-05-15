import ray
import os
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer
from reward import format_reward_func, kubectl_syntax_reward_func

# Connect to the running Kubernetes Ray Cluster Head Node
# Check if running in Volcano-scheduled environment
volcano_scheduled = os.environ.get('VOLCANO_JOB_NAME') is not None
if volcano_scheduled:
    print("🌋 Detected Volcano scheduler - optimizing for batch scheduling")
    
ray.init(address="auto", ignore_reinit_error=True)

model_id = "Qwen/Qwen2.5-7B-Instruct"
dataset = load_dataset("json", data_files="dataset.jsonl", split="train")

# Create TensorBoard logs directory
os.makedirs("ray_qwen_k8s_output/logs", exist_ok=True)

training_args = GRPOConfig(
    output_dir="ray_qwen_k8s_output",
    learning_rate=3e-6,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    num_train_epochs=2,
    report_to=["wandb", "tensorboard"], # Enable both WandB and TensorBoard logging
    logging_steps=1,
    bf16=True,           # Ampere/Hopper hardware acceleration matrix flag
    logging_dir="ray_qwen_k8s_output/logs",  # TensorBoard logs directory
)

trainer = GRPOTrainer(
    model=model_id,
    args=training_args,
    train_dataset=dataset,
    reward_funcs=[format_reward_func, kubectl_syntax_reward_func],
)

print("🚀 Starting training with TensorBoard monitoring...")
print("📊 View training progress at: http://localhost:6006")
print("📈 Monitor metrics: KL divergence, reward curves, loss values")
if volcano_scheduled:
    print("🌋 Volcano scheduler enabled for enhanced resource management")

trainer.train()
trainer.save_model("final_k8s_qwen_agent")
print("🎉 Model successfully optimized and saved to 'final_k8s_qwen_agent'")
print("📊 Final training metrics available in TensorBoard logs")
if volcano_scheduled:
    print("🌋 Volcano scheduling completed successfully")
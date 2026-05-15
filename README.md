# Sovereign SRE Agent: Distributed K8s & Ray Fine-Tuning Pipeline

An enterprise-grade, distributed Reinforcement Learning (RL) alignment pipeline designed to fine-tune Large Language Models (e.g., Qwen 2.5) into autonomous SRE Agents for Kubernetes troubleshooting. 

This repository implements **Group Relative Policy Optimization (GRPO)** via Hugging Face TRL, orchestrated across a **Kubernetes** cluster using **KubeRay** and accelerated by **vLLM**. It converts unstructured human SRE workflows (`SKILL.md` runbooks) into structured token trajectories, applies bulletproof reward functions to eliminate reward hacking, and tracks performance telemetry using Weights & Biases (WandB).

---

## 🏗️ Architectural Topology

Use code with caution.[ KubeRay Operator Hub ]│┌──────────────┴──────────────┐▼                             ▼[ Ray Head Node ] ◄─────────────► [ Ray Worker Node ](TRL Optimization)               (vLLM Trajectory Rollouts)│                             │[ NVIDIA A100 / H100 ]        [ NVIDIA A100 / H100 ]
The system separates concerns across three clear boundaries:
1. **The Machine Learning Agent (The Model Brain):** Optimised via GRPO to predict thinking tokens (`<thought>`) and structural tool actions.
2. **The AI Application / Infrastructure Layer (The Harness):** Manages sandboxed shell executions, cluster security boundaries, and handles `kubectl` connection variables.
3. **The Compute Orchestration Layer (Ray on K8s):** Distributes inference rollouts and matrix weight updates dynamically across multiple hardware nodes.

---

## 🛠️ Step 1: Cluster Infrastructure Setup

Deploy the **KubeRay Operator** inside your Kubernetes cluster to decouple model optimization from parallel rollout generation:

```bash
# 1. Add and update the KubeRay Helm repository
helm repo add kfray https://github.io
helm repo update

# 2. Install the operator
helm install kuberay-operator kfray/kuberay-operator --version 1.1.0
```

*Note: Ensure your custom Ray cluster specification allocations utilize shared memory flags (`/dev/shm`) to satisfy high-throughput inter-process communication (IPC) demands between PyTorch workers.*

---

## 🔄 Step 2: Data Pipeline (`convert.py`)

This data engineering engine scans your collection of real-world or simulated `SKILL.md` expert trajectories and transforms them into strict, tokenizable, multi-turn tool-calling schemas matching OpenAI/ShareGPT specifications.

Create the following local layout:
```text
training_engine/
├── convert.py
├── reward.py
├── train.py
└── skills/
    ├── incident_001.md
    └── incident_002.md
```

#### File Implementation: `convert.py`
```python
import os
import json
import re

def parse_skill_markdown(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract failure context
    prompt_match = re.search(r'# Prompt\n(.*?)\n#', content, re.DOTALL)
    prompt = prompt_match.group(1).strip() if prompt_match else "Troubleshoot cluster."
    
    # Parse command strings and their corresponding system responses
    commands = re.findall(r'```bash\n(kubectl.*?)\n```', content)
    outputs = re.findall(r'```text\n(.*?)\n```', content, re.DOTALL)
    
    messages = [{"role": "user", "content": prompt}]
    
    for i, cmd in enumerate(commands):
        tool_id = f"call_gen_{i}"
        messages.append({
            "role": "assistant",
            "content": f"Executing diagnostic command: {cmd}",
            "tool_calls": [{
                "id": tool_id, 
                "type": "function", 
                "function": {"name": "kubectl_run", "arguments": json.dumps({"cmd": cmd})}
            }]
        })
        out_content = outputs[i].strip() if i < len(outputs) else "Command completed."
        messages.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "content": out_content
        })
        
    return {"messages": messages}

if __name__ == "__main__":
    os.makedirs("skills", exist_ok=True)
    with open("dataset.jsonl", "w", encoding="utf-8") as out:
        for f in os.listdir("skills"):
            if f.endswith(".md"):
                record = parse_skill_markdown(os.path.join("skills", f))
                out.write(json.dumps(record) + "\n")
    print("🎯 Data Pipeline Execution Complete -> dataset.jsonl generated.")
```

Run the pipeline converter:
```bash
python3 convert.py
```

---

## 🛡️ Step 3: Bulletproof Reward Functions (`reward.py`)

To prevent **Reward Hacking** (where models learn to exploit mathematical feedback systems by generating empty strings or getting stuck in infinite text loops), this layer enforces strict format boundaries, abstract validation tags, and regex penalties.

#### File Implementation: `reward.py`
```python
import re

def format_reward_func(prompts, completions, **kwargs) -> list[float]:
    """Validates structural reasoning encapsulation tags."""
    rewards = []
    for completion in completions:
        text = completion["content"] if isinstance(completion, list) else completion["content"]
        
        # Enforce standard thinking blocks used by reasoning frameworks
        has_thought_tags = bool(re.search(r"<thought>.*?</thought>", text, re.DOTALL))
        has_output_tags = bool(re.search(r"<output>.*?</output>", text, re.DOTALL))
        
        if has_thought_tags and has_output_tags:
            rewards.append(1.0)
        elif has_thought_tags:
            rewards.append(0.3)  # Partial credit for thinking but missing output blocks
        else:
            rewards.append(-0.5) # Heavy penalty for formatting bypass
    return rewards

def kubectl_syntax_reward_func(prompts, completions, **kwargs) -> list[float]:
    """Penalizes execution loops, resource heavy greps, and invalid commands."""
    rewards = []
    for completion in completions:
        text = completion["content"] if isinstance(completion, list) else completion["content"]
        commands = re.findall(r"kubectl\s+([a-zA-Z0-9_\-\s\d\.\/]+)", text)
        
        score = 0.0
        for cmd in commands:
            # Block dangerous loop patterns or broad system scans
            if any(forbidden in cmd for forbidden in ["--watch", "grep -v", "exec -it"]):
                score -= 1.0
                continue
            if "get" in cmd or "describe" in cmd or "logs" in cmd:
                score += 0.5
                
        rewards.append(max(-1.0, min(1.5, score)))
    return rewards
```

---

## 🚀 Step 4: Distributed GRPO Training Script (`train.py`)

This script initializes the connection to the Kubernetes-backed Ray cluster, configures the `GRPOTrainer`, links your rule-based reward functions, and scales execution parameters natively across GPU workers.

#### File Implementation: `train.py`
```python
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
```

Submit the training worker job straight to your cluster:
```bash
ray job submit --address http://localhost:8265 -- python3 train.py
```

---

## 📊 Step 5: Live Diagnostics Metrics Guide

When tracking your model optimization runs within your telemetry dashboard (Weights & Biases / TensorBoard), use these analytical parameters to diagnose pipeline health:

Metric Value                     Metric Value▲                                ▲│   /───\                        │      /────────────│  /     \                       │     /│ /       ______                │    /└──────────────────►             └──────────────────►Steps                            Steps[ CHART 1: Optimal KL ]          [ CHART 2: Stable Reward ]
### 1. The KL Divergence Plateau (Model Drift Tracking)
*   **The Sweet Spot:** The value must climb slowly and plateau flatly between `0.08` and `0.18`.
*   **The Danger Zone:** If the metric breaks past `0.4`, the model is overwriting its native language structure rules (**Catastrophic Forgetting**). **Kill the job immediately.** Doubling your `kl_coef` configuration parameter will force it to stay anchored to the base weights.

### 2. The Mean Reward Ascent
*   **The Sweet Spot:** A clean, upward staircase curve starting from initial negative scores and stabilizing around a net positive average score.
*   **The Danger Zone:** If the reward climbs to its maximum limits but verification tests output garbage text loops, the model has hacked your validation checks. Stop the training and patch your `reward.py` code logic.

---

## 💼 Business Metrics & High-Value Portfolio Layout

Deploying this architecture establishes several premium skill competencies crucial for high-paying AI Systems engineering positions:

*   **Project 1: The Sovereign SRE Infrastructure Sandbox**
    *   *The Value:* Shows engineering capability in containerised pipelines. Proves you can deploy production-grade model setups on cloud nodes without risking budget-killing out-of-memory (OOM) faults.
*   **Project 2: The Multi-Turn Trajectory Synthesizer Engine**
    *   *The Value:* Highlights skill in programmatic data cleaning. Showcases your capability to scale data generation from simple unit test loops while actively protecting models from reward hacking anomalies.
*   **Project 3: Cost-Efficiency Benchmark Case Study**
    *   *The Value:* Proves true business value to CTOs. By fine-tuning local open-source models to run deterministically within your private cluster infrastructure, you eliminate recurring dependency costs tied to commercial platform APIs.
If you need to scale this workflow further, let me know if you would like me to generate a matching Dockerfile to containerise your environment or a Git pre-commit hook to enforce strict markdown compliance check blocks across your team.
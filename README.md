# Sovereign SRE Agent: Distributed K8s & Ray Fine-Tuning Pipeline

An enterprise-grade, distributed Reinforcement Learning (RL) alignment pipeline designed to fine-tune Large Language Models (e.g., Qwen 2.5) into autonomous SRE Agents for Kubernetes troubleshooting. 

This repository implements **Group Relative Policy Optimization (GRPO)** via Hugging Face TRL, orchestrated across a **Kubernetes** cluster using **KubeRay** and accelerated by **vLLM**. It converts unstructured human SRE workflows (`SKILL.md` runbooks) into structured token trajectories, applies bulletproof reward functions to eliminate reward hacking, and tracks performance telemetry using Weights & Biases (WandB).

---

## 🎯 Project Purpose

The Sovereign SRE Agent project aims to create autonomous AI agents capable of diagnosing and resolving Kubernetes infrastructure issues. By fine-tuning large language models with real-world SRE troubleshooting workflows, we create an intelligent system that can:

- **Analyze cluster issues** by executing diagnostic commands
- **Provide step-by-step troubleshooting** with reasoning capabilities
- **Execute safe remediation actions** based on learned patterns
- **Scale across distributed infrastructure** using Kubernetes and Ray

---

## 🔄 Relationship with HolmesGPT

This project builds upon **HolmesGPT** analysis results:

- **SKILL.md files** in `training_engine/skills/` are generated from HolmesGPT's incident analysis
- HolmesGPT provides the **raw troubleshooting expertise** that we convert into training data
- After fine-tuning, the resulting model becomes a **specialized SRE agent** focused on your specific infrastructure patterns

### Do you still need HolmesGPT after training?

**Yes, but for different purposes:**

1. **During Training:** HolmesGPT generates new SKILL.md files for expanding the training dataset
2. **Post-Training:** HolmesGPT serves as a **complementary tool** for:
   - Generating new training data for model updates
   - Handling edge cases the fine-tuned model hasn't seen
   - Providing human-in-the-loop oversight for critical incidents
   - Creating specialized agents for different infrastructure domains

The fine-tuned model becomes your **primary autonomous agent**, while HolmesGPT becomes your **expert system for continuous improvement**.

---

## 🏗️ Architectural Topology

The system separates concerns across three clear boundaries:

1. **The Machine Learning Agent (The Model Brain):** Optimised via GRPO to predict thinking tokens (`<thought>`) and structural tool actions.
2. **The AI Application / Infrastructure Layer (The Harness):** Manages sandboxed shell executions, cluster security boundaries, and handles `kubectl` connection variables.
3. **The Compute Orchestration Layer (Ray on K8s):** Distributes inference rollouts and matrix weight updates dynamically across multiple hardware nodes.

---

## 🚀 Quick Start Guide

### Prerequisites
- Kubernetes cluster with KubeRay operator installed
- Python 3.8+
- GPU nodes for training (recommended: NVIDIA A100/H100)

### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:huoqifeng/holmesgpt-ft.git
   cd holmesgpt-ft
   ```

2. **Install dependencies:**
   ```bash
   python3 setup.py
   ```

3. **Prepare your training data:**
   - Add HolmesGPT-generated incident documentation to `training_engine/skills/` as `.md` files
   - Run the data pipeline: `python3 training_engine/convert.py`

4. **Start training:**
   ```bash
   python3 training_engine/train.py
   ```

---

## 📁 Project Structure

```
.
├── training_engine/
│   ├── skills/           # HolmesGPT-generated incident documentation files
│   ├── convert.py        # Data pipeline for converting SKILL.md to training data
│   ├── reward.py         # Reward functions to prevent reward hacking
│   ├── train.py          # Distributed GRPO training script
│   ├── monitor.py        # Training monitoring with TensorBoard
│   └── dataset.jsonl     # Generated training dataset
├── Dockerfile            # Containerization configuration
├── manifest.yaml         # Kubernetes deployment manifests
├── requirements.txt      # Python dependencies
├── run_live_agent.py     # Interactive agent testing interface
├── setup.py             # Automated setup script
└── README.md            # This documentation
```

---

## 🛠️ Core Components

### 1. Data Pipeline (`convert.py`)
Transforms HolmesGPT-generated SRE incident runbooks into structured, tokenizable training data that follows OpenAI/ShareGPT specifications.

### 2. Reward Functions (`reward.py`)
Implements bulletproof reward mechanisms to prevent reward hacking and ensure the model learns proper troubleshooting patterns from HolmesGPT expertise.

### 3. Training Engine (`train.py`)
Distributed GRPO training script that orchestrates model fine-tuning across Kubernetes cluster using Ray, converting HolmesGPT knowledge into autonomous capabilities.

### 4. Training Monitor (`monitor.py`)
Real-time training monitoring with TensorBoard integration for visualizing KL divergence, reward curves, and training metrics.

### 5. Live Agent (`run_live_agent.py`)
Interactive interface for testing the trained model with real Kubernetes troubleshooting scenarios.

---

## 📊 Monitoring & Metrics

### Real-time Training Monitoring

This project includes comprehensive monitoring capabilities through **TensorBoard** and **Weights & Biases**:

#### TensorBoard Monitoring
```bash
# Start TensorBoard during training
tensorboard --logdir ray_qwen_k8s_output/logs --port 6006

# Or use the built-in monitor
python3 training_engine/monitor.py --port 6006
```

#### Available Metrics Dashboards:
- **KL Divergence**: Track model drift and prevent catastrophic forgetting
- **Reward Curves**: Monitor reward ascent and detect reward hacking
- **Loss Values**: Observe training convergence
- **Gradient Norms**: Detect training instability

#### Key Metrics to Watch:

### KL Divergence Plateau (Model Drift Tracking)
- **Sweet Spot:** Value should plateau between `0.08` and `0.18`
- **Danger Zone:** If value exceeds `0.4`, stop training immediately (catastrophic forgetting)

### Mean Reward Ascent
- **Sweet Spot:** Clean upward staircase curve stabilizing around net positive scores
- **Danger Zone:** If reward maxes out but outputs garbage, the model has hacked validation

### Monitoring Commands
```bash
# Start monitoring during training
python3 training_engine/monitor.py

# Start TensorBoard separately
tensorboard --logdir ray_qwen_k8s_output/logs

# Monitor with custom port
python3 training_engine/monitor.py --port 8080
```



---

## 🏢 Business Value

This project establishes several premium skill competencies:

1. **Sovereign SRE Infrastructure Sandbox** - Demonstrates containerized pipeline engineering
2. **Multi-Turn Trajectory Synthesizer Engine** - Showcases programmatic data cleaning at scale
3. **Cost-Efficiency Benchmark Case Study** - Eliminates recurring API costs with local open-source models

---

## 🔧 Advanced Usage

### Container Deployment
```bash
docker build -t holmesgpt-ft .
docker run -p 8265:8265 holmesgpt-ft
```

### Kubernetes Deployment
```bash
kubectl apply -f manifest.yaml
```

### Ray Job Submission
```bash
ray job submit --address http://localhost:8265 -- python3 training_engine/train.py
```

---

## 📈 Next Steps

1. **Generate SKILL.md files** using HolmesGPT analysis on your infrastructure incidents
2. **Customize reward functions** in `training_engine/reward.py` for your specific use case
3. **Scale training infrastructure** across multiple GPU nodes
4. **Integrate with existing monitoring systems** for production deployment
5. **Continuously improve** by feeding new HolmesGPT analysis results back into training

For detailed implementation guidance, refer to the individual component files in the `training_engine/` directory.
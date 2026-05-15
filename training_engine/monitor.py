#!/usr/bin/env python3
"""
Training Monitor for HolmesGPT Fine-Tuning Pipeline
Provides TensorBoard monitoring and real-time training metrics visualization
"""

import os
import json
import time
import threading
from datetime import datetime
import subprocess
from pathlib import Path

class TrainingMonitor:
    def __init__(self, log_dir="ray_qwen_k8s_output/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.tensorboard_process = None
        
    def start_tensorboard(self, port=6006):
        """Start TensorBoard server"""
        print(f"🚀 Starting TensorBoard on port {port}...")
        cmd = [
            "tensorboard",
            "--logdir", str(self.log_dir),
            "--port", str(port),
            "--host", "0.0.0.0",
            "--reload_interval", "10"
        ]
        
        try:
            self.tensorboard_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"✅ TensorBoard started at http://localhost:{port}")
            return True
        except Exception as e:
            print(f"❌ Failed to start TensorBoard: {e}")
            return False
    
    def stop_tensorboard(self):
        """Stop TensorBoard server"""
        if self.tensorboard_process:
            self.tensorboard_process.terminate()
            self.tensorboard_process.wait()
            print("🛑 TensorBoard stopped")
    
    def monitor_training(self, check_interval=30):
        """Monitor training progress and log metrics"""
        print("📊 Starting training monitor...")
        
        while True:
            try:
                # Check if training is active
                training_active = self._check_training_activity()
                
                if training_active:
                    metrics = self._collect_metrics()
                    self._log_metrics(metrics)
                    print(f"📈 Training active - KL: {metrics.get('kl', 'N/A')}, Reward: {metrics.get('reward', 'N/A')}")
                else:
                    print("⏸️  No active training detected")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Training monitor stopped")
                break
            except Exception as e:
                print(f"⚠️  Monitor error: {e}")
                time.sleep(check_interval)
    
    def _check_training_activity(self):
        """Check if training is currently active"""
        # Check for recent log files
        log_files = list(self.log_dir.glob("**/*.json"))
        if not log_files:
            return False
        
        # Check if any log file was modified recently
        recent_threshold = time.time() - 300  # 5 minutes
        for log_file in log_files:
            if log_file.stat().st_mtime > recent_threshold:
                return True
        return False
    
    def _collect_metrics(self):
        """Collect current training metrics from log files"""
        metrics = {}
        
        # Look for the most recent metrics file
        metrics_files = list(self.log_dir.glob("**/metrics.json"))
        if metrics_files:
            latest_file = max(metrics_files, key=lambda x: x.stat().st_mtime)
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    metrics.update(data)
            except Exception as e:
                print(f"⚠️  Failed to read metrics: {e}")
        
        return metrics
    
    def _log_metrics(self, metrics):
        """Log metrics to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "metrics": metrics
        }
        
        # Log to console
        if "kl" in metrics and "reward" in metrics:
            print(f"[{timestamp}] KL: {metrics['kl']:.4f}, Reward: {metrics['reward']:.4f}")
        
        # Log to file
        monitor_log = self.log_dir / "monitor.log"
        with open(monitor_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Training Monitor for HolmesGPT")
    parser.add_argument("--port", type=int, default=6006, help="TensorBoard port")
    parser.add_argument("--no-tensorboard", action="store_true", help="Don't start TensorBoard")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    monitor = TrainingMonitor()
    
    # Start TensorBoard unless disabled
    if not args.no_tensorboard:
        monitor.start_tensorboard(args.port)
    
    try:
        # Start monitoring
        monitor.monitor_training(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down monitor...")
    finally:
        monitor.stop_tensorboard()

if __name__ == "__main__":
    main()
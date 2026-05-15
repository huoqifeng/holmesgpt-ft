#!/usr/bin/env python3
"""
Setup script for HolmesGPT Fine-Tuning Pipeline
"""

import os
import subprocess
import sys

def install_requirements():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_training_data():
    """Set up training data by running the convert script."""
    print("Setting up training data...")
    os.chdir("training_engine")
    subprocess.check_call([sys.executable, "convert.py"])
    os.chdir("..")

def main():
    print("Setting up HolmesGPT Fine-Tuning Pipeline...")
    
    try:
        install_requirements()
        setup_training_data()
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Ensure you have a Kubernetes cluster with KubeRay installed")
        print("2. Run 'python3 training_engine/train.py' to start training")
        print("3. Or use 'python3 run_live_agent.py --interactive' to test the agent")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
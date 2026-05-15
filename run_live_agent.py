#!/usr/bin/env python3
"""
Live Agent Runner for HolmesGPT Fine-Tuned Model
This script loads the trained model and provides an interactive interface
for troubleshooting Kubernetes issues.
"""

import os
import json
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def load_trained_model(model_path="final_k8s_qwen_agent"):
    """Load the fine-tuned model and tokenizer."""
    print(f"Loading model from {model_path}...")
    
    if not os.path.exists(model_path):
        print(f"Model path {model_path} does not exist. Using base model.")
        model_path = "Qwen/Qwen2.5-7B-Instruct"
    
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    return tokenizer, model

def generate_response(tokenizer, model, prompt, max_length=2048):
    """Generate a response from the model."""
    messages = [
        {"role": "system", "content": "You are an expert Kubernetes SRE agent. Analyze the issue and provide step-by-step troubleshooting guidance."},
        {"role": "user", "content": prompt}
    ]
    
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response

def main():
    parser = argparse.ArgumentParser(description="Run HolmesGPT Fine-Tuned Agent")
    parser.add_argument("--model-path", default="final_k8s_qwen_agent", help="Path to the trained model")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--prompt", help="Single prompt to process")
    
    args = parser.parse_args()
    
    tokenizer, model = load_trained_model(args.model_path)
    
    if args.interactive:
        print("HolmesGPT Agent - Interactive Mode")
        print("Type 'quit' or 'exit' to stop")
        print("-" * 50)
        
        while True:
            try:
                prompt = input("\nEnter your Kubernetes issue: ").strip()
                if prompt.lower() in ['quit', 'exit']:
                    break
                
                if not prompt:
                    continue
                
                print("\n<thought>")
                response = generate_response(tokenizer, model, prompt)
                print(response)
                print("</thought>")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    elif args.prompt:
        print(f"Processing prompt: {args.prompt}")
        response = generate_response(tokenizer, model, args.prompt)
        print("\n<thought>")
        print(response)
        print("</thought>")
    
    else:
        print("No mode specified. Use --interactive or --prompt")

if __name__ == "__main__":
    main()
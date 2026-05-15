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
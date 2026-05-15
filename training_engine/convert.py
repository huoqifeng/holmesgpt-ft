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
import os
import re
import sys
from pathlib import Path
import yaml

def strip_front_matter(text: str) -> str:
    # Remove a leading YAML front matter block if present: --- ... ---
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + len("\n---\n"):]
    return text

def extract_tasks_yaml(md_text: str) -> str:
    body = strip_front_matter(md_text)
    m = re.search(r"(?m)^tasks:\s*$", body)
    if not m:
        raise SystemExit("Could not find top-level 'tasks:' in tasks.md body.")
    return body[m.start():]

def load_tasks(tasks_md_path: Path) -> list[dict]:
    md_text = tasks_md_path.read_text(encoding="utf-8")
    yaml_text = extract_tasks_yaml(md_text)
    data = yaml.safe_load(yaml_text) or {}
    tasks = data.get("tasks", [])
    if not isinstance(tasks, list):
        raise SystemExit("'tasks' is not a list — check indentation in tasks.md.")
    return tasks

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python ralph_extract.py <path-to-tasks.md>")
    tasks_path = Path(sys.argv[1]).expanduser()
    tasks = load_tasks(tasks_path)
    print(yaml.safe_dump(tasks, sort_keys=False))

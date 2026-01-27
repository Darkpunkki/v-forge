import sys
from pathlib import Path
import yaml
from ralph_extract import load_tasks

STATE_FILE = Path("ralph_state.yaml")

def load_state():
    if not STATE_FILE.exists():
        return {"done": [], "blocked": {}, "attempts": {}}
    return yaml.safe_load(STATE_FILE.read_text(encoding="utf-8")) or {"done": [], "blocked": {}, "attempts": {}}

def deps_satisfied(task, done_set):
    deps = task.get("dependencies") or []
    return all(d in done_set for d in deps)

def prio_key(t):
    return (t.get("priority", "P9"), t.get("id", ""))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python ralph_pick.py <path-to-tasks.md>")

    tasks_path = Path(sys.argv[1]).expanduser()
    tasks = load_tasks(tasks_path)

    state = load_state()
    done = set(state.get("done", []))

    eligible = [t for t in tasks if t.get("id") not in done and deps_satisfied(t, done)]
    eligible.sort(key=prio_key)

    if not eligible:
        print("RALPH_DONE")
    else:
        print(yaml.safe_dump(eligible[0], sort_keys=False))

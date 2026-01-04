"""Mock generator for MVP demo - creates simple demo files."""

import os
from pathlib import Path
from typing import Any


class MockGenerator:
    """Generates mock demo files based on BuildSpec."""

    @staticmethod
    def generate(session_id: str, build_spec: dict[str, Any], workspace_path: Path) -> list[str]:
        """
        Generate mock files in the workspace.

        Returns list of files generated.
        """
        repo_path = workspace_path / "repo"
        repo_path.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Extract info from BuildSpec
        platform = build_spec["target"]["platform"]
        preset = build_spec["stack"]["preset"]
        genre = build_spec["ideaSeed"]["genre"]
        twists = build_spec["ideaSeed"]["twists"]

        # Generate appropriate files based on platform
        if preset == "WEB_VITE_REACT_TS":
            generated_files = _generate_web_vite_react(repo_path, genre, twists)
        elif preset == "CLI_PYTHON":
            generated_files = _generate_cli_python(repo_path, genre, twists)
        else:
            # Default to simple README
            generated_files = _generate_basic_project(repo_path, platform, genre)

        return generated_files


def _generate_web_vite_react(repo_path: Path, genre: str, twists: list[str]) -> list[str]:
    """Generate a mock Vite+React project."""
    files = []

    # package.json
    package_json_content = """{
  "name": "vibeforge-demo-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "typescript": "^5.0.0"
  }
}
"""
    _write_file(repo_path / "package.json", package_json_content)
    files.append("package.json")

    # index.html
    index_html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VibeForge Demo App</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
"""
    _write_file(repo_path / "index.html", index_html_content)
    files.append("index.html")

    # src/main.tsx
    src_dir = repo_path / "src"
    src_dir.mkdir(exist_ok=True)

    twist_comment = f"// Twists: {', '.join(twists)}" if twists else ""

    main_tsx_content = f"""import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// VibeForge Generated App
// Genre: {genre}
{twist_comment}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
    _write_file(src_dir / "main.tsx", main_tsx_content)
    files.append("src/main.tsx")

    # src/App.tsx
    app_tsx_content = f"""import React from 'react';

function App() {{
  return (
    <div style={{{{ padding: '2rem', fontFamily: 'sans-serif' }}}}>
      <h1>VibeForge Demo: {genre}</h1>
      <p>This is a generated {genre.lower()} application.</p>
      {_generate_twist_jsx(twists)}
    </div>
  );
}}

export default App;
"""
    _write_file(src_dir / "App.tsx", app_tsx_content)
    files.append("src/App.tsx")

    # README.md
    readme_content = f"""# VibeForge Demo App

This is a generated demo application.

**Genre:** {genre}
**Twists:** {', '.join(twists) if twists else 'None'}

## Run Instructions

```bash
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Build

```bash
npm run build
```

## Test

```bash
npm test
```
"""
    _write_file(repo_path / "README.md", readme_content)
    files.append("README.md")

    return files


def _generate_cli_python(repo_path: Path, genre: str, twists: list[str]) -> list[str]:
    """Generate a mock Python CLI project."""
    files = []

    # main.py
    twist_comment = f"# Twists: {', '.join(twists)}" if twists else ""

    main_py_content = f"""#!/usr/bin/env python3
\"\"\"VibeForge Demo CLI - {genre}\"\"\"

import argparse

# Genre: {genre}
{twist_comment}

def main():
    parser = argparse.ArgumentParser(description='VibeForge Demo CLI')
    parser.add_argument('--version', action='version', version='1.0.0')
    args = parser.parse_args()

    print(f"VibeForge Demo: {genre}")
    print("This is a generated demo application.")

if __name__ == '__main__':
    main()
"""
    _write_file(repo_path / "main.py", main_py_content)
    files.append("main.py")

    # requirements.txt
    requirements_content = "# Add your dependencies here\n"
    _write_file(repo_path / "requirements.txt", requirements_content)
    files.append("requirements.txt")

    # README.md
    readme_content = f"""# VibeForge Demo CLI

This is a generated demo CLI application.

**Genre:** {genre}
**Twists:** {', '.join(twists) if twists else 'None'}

## Run Instructions

```bash
python main.py --help
```

## Test

```bash
python -m pytest
```
"""
    _write_file(repo_path / "README.md", readme_content)
    files.append("README.md")

    return files


def _generate_basic_project(repo_path: Path, platform: str, genre: str) -> list[str]:
    """Generate a basic README-only project."""
    readme_content = f"""# VibeForge Demo

Platform: {platform}
Genre: {genre}

This is a placeholder project generated by VibeForge.
"""
    _write_file(repo_path / "README.md", readme_content)
    return ["README.md"]


def _generate_twist_jsx(twists: list[str]) -> str:
    """Generate JSX for twists."""
    if not twists:
        return ""

    twist_items = "".join([f"        <li>{twist.replace('_', ' ').title()}</li>\n" for twist in twists])

    return f"""      <h2>Features</h2>
      <ul>
{twist_items}      </ul>"""


def _write_file(path: Path, content: str):
    """Write content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# Global instance
mock_generator = MockGenerator()

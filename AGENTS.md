# Repository Guidelines

## Project Structure & Module Organization
- `py_packager_gui.py` is the main PySide6 GUI application that orchestrates packaging for Python, C#, Node.js, and Java.
- `py_packager_gui.spec` is the PyInstaller spec used to build the GUI into a standalone executable.
- `build/` and `dist/` are generated build outputs; treat them as artifacts and avoid editing by hand.

## Build, Test, and Development Commands
- `python py_packager_gui.py` runs the GUI locally for development.
- `pyinstaller py_packager_gui.spec` builds the GUI into `dist/` (requires PyInstaller).
- Inside the app, packaging commands are invoked through the GUI:
  - Python: `python -m PyInstaller <entry> --onefile --noconsole --clean`
  - C#: `dotnet publish <project>.csproj -c Release -r win-x64 --output dist`
  - Node.js: `npx pkg <entry> --targets node18-win-x64 --out-path dist`
  - Java: `jpackage --input <dir> --main-jar <jar> --type <type> --dest dist`

## Coding Style & Naming Conventions
- Indentation is 4 spaces; keep lines readable and avoid overly long chains.
- Class names use `CamelCase` (e.g., `MultiPackagerApp`); functions and variables use `snake_case`.
- UI text is localized via the `self.trans` dictionary; add both `en` and `zh` entries for new strings.

## Testing Guidelines
- There is no automated test suite in this repository.
- If you add tests, prefer `pytest` and place them under a new `tests/` directory (e.g., `tests/test_packager_ui.py`).

## Commit & Pull Request Guidelines
- This directory is not a Git repository and has no commit history to infer conventions.
- If you initialize Git, use short, imperative commit messages (e.g., `Add language toggle`) and include a brief PR description with screenshots for UI changes.

## Configuration Tips
- Ensure required build tools are on `PATH`: PyInstaller, .NET SDK (`dotnet`), Node.js (`npm`/`npx`), and JDK with `jpackage`.

# Universal Code Packager (MultiPackagerApp)

## Project Overview
This project is a **PySide6-based GUI application** designed to simplify the process of packaging code for distribution. It acts as a unified interface for various build tools, allowing users to package applications written in **Python, C#, Node.js, and Java** into standalone executables or distributable formats.

**Latest Update (2026-01-03):** 
- Refactored from a monolithic script into a modular architecture.
- Added **Type Safety** via `dataclasses` for configuration.
- Added **Unit Tests** (`tests/test_builders.py`).
- Improved **Resource Handling** for frozen (PyInstaller) environments.

## Key Features
*   **Multi-Language Support:**
    *   **Python:** Wraps `PyInstaller` & `Nuitka` (Supports clean builds, console/GUI toggles). **New:** Auto-detects interpreter in frozen environments.
    *   **C# (.NET):** Wraps `dotnet publish`. **New:** Selectable Target Runtime (RID) (e.g., win-x64, linux-x64).
    *   **Node.js:** Wraps `pkg` via `npx`.
    *   **Java:** Wraps `jpackage`.
*   **Modular Architecture:** Logic, UI, and Resources are separated for better maintainability.
*   **Externalized Translations:** Translations are stored in `src/resources/translations.json`.

## Prerequisites

### Python Dependencies
*   `PySide6`
*   `PyInstaller` (for building the tool)
*   `Nuitka` (optional, for Python packaging)

### External Build Tools
*   **C#:** .NET SDK (`dotnet`)
*   **Node.js:** Node.js & npm (`npx`)
*   **Java:** JDK 14+ (`jpackage`)

## Project Structure
```text
compass/
├── src/
│   ├── main.py                 # Application Entry Point
│   ├── core/
│   │   ├── builders.py         # Core build logic (Logic)
│   │   ├── config.py           # Configuration Data Classes (Model)
│   │   ├── utils.py            # Path & Resource Helpers
│   │   └── __init__.py
│   ├── ui/
│   │   ├── main_window.py      # Main GUI Class (View)
│   │   └── __init__.py
│   ├── resources/
│   │   └── translations.json   # Externalized Strings (EN/ZH)
│   └── __init__.py
├── tests/
│   └── test_builders.py        # Unit Tests for Core Logic
├── backup/                     # Old monolithic version
└── GEMINI.md
```

## Usage

### Running Locally
To launch the application from source:
```bash
python -m src.main
```

### Running Tests
To verify the build logic:
```bash
python tests/test_builders.py
```

### Building the Application
To package the GUI itself into an EXE using PyInstaller:
```bash
pyinstaller --name "CompassPackager" --noconsole --add-data "src/resources/translations.json;src/resources" src/main.py
```

## Developer Notes
*   **Adding Languages:** 
    1. Define a config dataclass in `src/core/config.py`.
    2. Add a builder method in `src/core/builders.py`.
    3. Add a setup method in `src/ui/main_window.py`.
*   **Localization:** Add new keys to `src/resources/translations.json`.

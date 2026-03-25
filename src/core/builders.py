import sys
import os
import shutil

from .android_project import build_android_project

class Builder:
    """
    Core logic for building applications.
    Decoupled from UI to allow testing and CLI usage.
    """
    
    @staticmethod
    def check_tool(cmd_name):
        return shutil.which(cmd_name) is not None

    @staticmethod
    def build_python(config: 'PythonConfig'):
        """
        Build Python application using PyInstaller or Nuitka.
        """
        entry = config.entry
        if not entry or not os.path.exists(entry):
            raise ValueError("Invalid entry file.")

        project_dir = os.path.dirname(entry)
        backend = config.backend
        interpreter = config.interpreter or ""

        # Resolve interpreter
        if interpreter and getattr(sys, 'frozen', False):
            # Guard against accidentally using the GUI exe as the interpreter.
            if os.path.abspath(interpreter) == os.path.abspath(sys.executable):
                interpreter = ""

        if not interpreter or not os.path.exists(interpreter):
            # If running frozen, sys.executable is the app exe, not python.
            if getattr(sys, 'frozen', False):
                # Try to find a real python interpreter in PATH
                found_python = None
                for py_cmd in ["python", "python3", "py"]:
                    p = shutil.which(py_cmd)
                    if p and os.path.abspath(p) != os.path.abspath(sys.executable):
                        found_python = p
                        break

                if found_python:
                    interpreter = found_python
                else:
                    raise RuntimeError("Python interpreter not found in PATH. Please specify path to python.exe in the 'Interpreter' field.")
            else:
                interpreter = sys.executable

        cmd = []
        
        if backend == 'nuitka':
            if "WindowsApps" in interpreter:
                raise RuntimeError("Nuitka does not support Windows Store Python.")

            cmd = [interpreter, "-m", "nuitka", "--follow-imports", "--assume-yes-for-downloads", "--show-scons"]
            
            if config.onefile:
                cmd.append("--onefile")
            else:
                cmd.append("--standalone")
                
            if config.noconsole:
                cmd.append("--windows-disable-console")
                
            if config.clean:
                cmd.append("--remove-output")
                
            cmd.append(f"--output-dir={os.path.join(project_dir, 'dist')}")
            cmd.append(entry)
            
        else: # PyInstaller
            # If we are running frozen, we can use the 'pyinstaller' command if in PATH,
            # OR use the specified interpreter module.
            if getattr(sys, 'frozen', False):
                # Try finding pyinstaller executable
                if shutil.which("pyinstaller"):
                     cmd = ["pyinstaller"]
                else:
                     # Fallback to module execution via interpreter
                     cmd = [interpreter, "-m", "PyInstaller"]
            else:
                cmd = [interpreter, "-m", "PyInstaller"]

            cmd.append(entry)
            
            if config.onefile: cmd.append("--onefile")
            if config.noconsole: cmd.append("--noconsole")
            if config.clean: cmd.append("--clean")
            
            dist = os.path.join(project_dir, "dist")
            work = os.path.join(project_dir, "build")
            cmd.append(f"--distpath={dist}")
            cmd.append(f"--workpath={work}")
            cmd.append(f"--specpath={project_dir}")

        return cmd, project_dir

    @staticmethod
    def build_csharp(config: 'CSharpConfig'):
        """
        Build C# application using dotnet publish.
        """
        if not Builder.check_tool("dotnet"):
            raise RuntimeError("dotnet tool not found in PATH.")

        proj = config.project_path
        if not proj or not os.path.exists(proj):
            raise ValueError("Invalid project file.")

        project_dir = os.path.dirname(proj)
        rid = config.rid
        
        cmd = ["dotnet", "publish", proj, "-c", "Release", "-r", rid]
        
        if config.self_contained:
            cmd.append("--self-contained=true")
        else:
            cmd.append("--self-contained=false")
            
        if config.single_file:
            cmd.append("-p:PublishSingleFile=true")
            
        if config.trim:
            cmd.append("-p:PublishTrimmed=true")
            
        output_dir = os.path.join(project_dir, "dist", rid)
        cmd.append(f"--output={output_dir}")
        
        return cmd, project_dir

    @staticmethod
    def build_node(config: 'NodeConfig'):
        """
        Build Node.js application using pkg.
        """
        if not Builder.check_tool("npx") and not Builder.check_tool("npm"):
            raise RuntimeError("Node.js (npm/npx) not found.")

        entry = config.entry
        if not entry or not os.path.exists(entry):
            raise ValueError("Invalid entry file.")
            
        project_dir = os.path.dirname(entry)
        target = config.target
        
        # Use npx.cmd on Windows
        npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
        
        cmd = [npx_cmd, "pkg", entry, "--targets", target, "--out-path", "dist"]
        
        return cmd, project_dir

    @staticmethod
    def build_java(config: 'JavaConfig'):
        """
        Build Java application using jpackage.
        """
        if not Builder.check_tool("jpackage"):
            raise RuntimeError("jpackage (JDK) not found.")
            
        input_path = config.input_path
        if not input_path or not os.path.exists(input_path):
            raise ValueError("Invalid input path.")
            
        main_jar = config.main_jar
        project_dir = input_path # Usually input path is the project build dir
        
        name = os.path.splitext(main_jar)[0]
        
        cmd = ["jpackage", "--input", input_path, "--main-jar", main_jar, "--name", name]
        
        if config.main_class:
            cmd.append(f"--main-class={config.main_class}")
            
        cmd.append(f"--type={config.output_type}")
        cmd.append(f"--dest={os.path.join(project_dir, 'dist')}")
        
        return cmd, project_dir

    @staticmethod
    def build_android(config: 'AndroidConfig'):
        """
        Generate an Android Studio project from a local web folder and optionally
        prepare a Gradle build command for APK/AAB output.
        """
        return build_android_project(config)

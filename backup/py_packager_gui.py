import sys
import os
import shutil
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QFileDialog, QCheckBox, QTextEdit, QGroupBox, QMessageBox, QComboBox, QStackedWidget, QFormLayout)
from PySide6.QtCore import QProcess, Qt

class MultiPackagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = 'zh' # Default Chinese
        
        # Define language options
        self.languages = ['Python', 'C# (.NET)', 'Node.js (JS)', 'Java']
        
        self.init_translations()
        self.init_ui()
        self.update_ui_text()

    def init_translations(self):
        self.trans = {
            'en': {
                'window_title': "Universal Code Packager (Python, C#, Node, Java)",
                'lang_switch_btn': "Language: English",
                'group_general': "General Settings",
                'label_target_lang': "Target Language:",
                'group_config': "Configuration",
                
                # Common
                'btn_browse_file': "Browse File...",
                'btn_browse_folder': "Browse Folder...",
                'btn_build': "Start Build",
                'log_placeholder': "Build logs will appear here...",
                'msg_success': "Build Completed Successfully!",
                'msg_fail': "Build Failed! Check logs.",
                
                # Python
                'py_input_label': "Script/Folder:",
                'py_input_ph': "Select .py file or folder",
                'py_entry_label': "Entry Point:",
                'py_backend_label': "Engine (Protection):",
                'py_onefile': "One File (--onefile)",
                'py_noconsole': "No Console (GUI Mode)",
                'py_clean': "Clean Build",
                
                # C#
                'cs_input_label': "Project File (.csproj):",
                'cs_input_ph': "Select .csproj file",
                'cs_self_contained': "Self Contained (No .NET required)",
                'cs_single_file': "Produce Single File",
                'cs_trim': "Trim Unused Code (Smaller Size)",
                
                # Node.js
                'node_input_label': "Entry File / package.json:",
                'node_input_ph': "Select .js or package.json",
                'node_target_label': "Target Node Version:",
                
                # Java
                'java_input_label': "Main JAR / Folder:",
                'java_input_ph': "Select .jar file",
                'java_main_class': "Main Class (optional for executable jar):",
                'java_type_label': "Output Type:",
                
                # Errors
                'err_title': "Error",
                'err_no_input': "Please select an input file/project.",
                'err_tool_missing': "Build tool '{}' not found in PATH.\nPlease install it first.",
                'err_store_python': "Nuitka does not support Windows Store Python.\nPlease install the official Python from python.org.",
            },
            'zh': {
                'window_title': "通用代码打包工具 (Python, C#, Node, Java)",
                'lang_switch_btn': "语言: 中文",
                'group_general': "通用设置",
                'label_target_lang': "目标语言:",
                'group_config': "详细配置",
                
                # Common
                'btn_browse_file': "浏览文件...",
                'btn_browse_folder': "浏览文件夹...",
                'btn_build': "开始构建",
                'log_placeholder': "构建日志将显示在这里...",
                'msg_success': "构建成功完成！",
                'msg_fail': "构建失败！请检查日志。",
                
                # Python
                'py_input_label': "脚本/文件夹:",
                'py_input_ph': "选择 .py 文件或文件夹",
                'py_entry_label': "入口文件:",
                'py_backend_label': "打包引擎 (保护强度):",
                'py_onefile': "单文件 (--onefile)",
                'py_noconsole': "无控制台 (GUI模式)",
                'py_clean': "清理构建",
                
                # C#
                'cs_input_label': "项目文件 (.csproj):",
                'cs_input_ph': "选择 .csproj 文件",
                'cs_self_contained': "独立部署 (无需安装 .NET)",
                'cs_single_file': "生成单文件",
                'cs_trim': "裁剪未使用代码 (更小体积)",
                
                # Node.js
                'node_input_label': "入口文件 / package.json:",
                'node_input_ph': "选择 .js 或 package.json",
                'node_target_label': "目标 Node 版本:",
                
                # Java
                'java_input_label': "主 JAR / 文件夹:",
                'java_input_ph': "选择 .jar 文件",
                'java_main_class': "主类 (可执行JAR可选):",
                'java_type_label': "输出类型:",
                
                # Errors
                'err_title': "错误",
                'err_no_input': "请先选择输入文件或项目。",
                'err_tool_missing': "未在环境变量中找到构建工具 '{}'。\n请确保已安装该语言的开发环境。",
                'err_store_python': "Nuitka 不支持微软商店版 Python (WindowsApps)。\n请去 python.org 下载安装官方版本。",
            }
        }

    def tr(self, key):
        return self.trans[self.current_lang].get(key, key)

    def init_ui(self):
        self.resize(800, 650)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Top Bar (Language Switch) ---
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.lang_btn = QPushButton()
        self.lang_btn.setFixedWidth(120)
        self.lang_btn.clicked.connect(self.toggle_language)
        top_bar.addWidget(self.lang_btn)
        main_layout.addLayout(top_bar)

        # --- General Settings (Language Selector) ---
        self.general_group = QGroupBox()
        general_layout = QHBoxLayout()
        
        self.label_lang = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.languages)
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        
        general_layout.addWidget(self.label_lang)
        general_layout.addWidget(self.lang_combo)
        general_layout.addStretch()
        
        self.general_group.setLayout(general_layout)
        main_layout.addWidget(self.general_group)

        # --- Configuration Stack (Dynamic UI) ---
        self.config_group = QGroupBox()
        config_layout = QVBoxLayout()
        
        self.stack = QStackedWidget()
        
        # 1. Python UI
        self.page_py = QWidget()
        self.setup_python_ui(self.page_py)
        self.stack.addWidget(self.page_py)
        
        # 2. C# UI
        self.page_cs = QWidget()
        self.setup_csharp_ui(self.page_cs)
        self.stack.addWidget(self.page_cs)
        
        # 3. Node.js UI
        self.page_node = QWidget()
        self.setup_node_ui(self.page_node)
        self.stack.addWidget(self.page_node)
        
        # 4. Java UI
        self.page_java = QWidget()
        self.setup_java_ui(self.page_java)
        self.stack.addWidget(self.page_java)
        
        config_layout.addWidget(self.stack)
        self.config_group.setLayout(config_layout)
        main_layout.addWidget(self.config_group)

        # --- Logs and Action ---
        self.build_btn = QPushButton()
        self.build_btn.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #2E8B57; color: white; border-radius: 4px;")
        self.build_btn.clicked.connect(self.start_build)
        main_layout.addWidget(self.build_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("font-family: Consolas, monospace; font-size: 12px; background-color: #1E1E1E; color: #D4D4D4;")
        main_layout.addWidget(self.log_output)

        # Process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

    # --- UI Setup Helpers ---
    def setup_python_ui(self, widget):
        layout = QFormLayout()
        
        # Input
        file_layout = QHBoxLayout()
        self.py_input = QLineEdit()
        btn_file = QPushButton("File")
        btn_file.clicked.connect(lambda: self.browse_file(self.py_input, "Python Files (*.py)"))
        btn_folder = QPushButton("Folder")
        btn_folder.clicked.connect(lambda: self.browse_folder(self.py_input))
        file_layout.addWidget(self.py_input)
        file_layout.addWidget(btn_file)
        file_layout.addWidget(btn_folder)
        self.py_input_label = QLabel()
        layout.addRow(self.py_input_label, file_layout)

        # Entry Point
        self.py_entry = QComboBox()
        self.py_entry.setEditable(True)
        self.py_entry_label = QLabel()
        layout.addRow(self.py_entry_label, self.py_entry)

        # Backend Selection
        self.py_backend = QComboBox()
        self.py_backend.addItems(["PyInstaller (Standard)", "Nuitka (High Security - C++)"])
        self.py_backend_label = QLabel()
        layout.addRow(self.py_backend_label, self.py_backend)
        
        # Checkboxes
        self.py_onefile = QCheckBox()
        self.py_onefile.setChecked(True)
        self.py_noconsole = QCheckBox()
        self.py_clean = QCheckBox()
        self.py_clean.setChecked(True)
        
        layout.addRow("", self.py_onefile)
        layout.addRow("", self.py_noconsole)
        layout.addRow("", self.py_clean)
        
        widget.setLayout(layout)
        
        # Auto-scan trigger
        self.py_input.textChanged.connect(lambda text: self.scan_python_entry(text))

    def setup_csharp_ui(self, widget):
        layout = QFormLayout()
        
        file_layout = QHBoxLayout()
        self.cs_input = QLineEdit()
        btn = QPushButton("Browse")
        btn.clicked.connect(lambda: self.browse_file(self.cs_input, "C# Project (*.csproj)"))
        file_layout.addWidget(self.cs_input)
        file_layout.addWidget(btn)
        
        self.cs_input_label = QLabel()
        layout.addRow(self.cs_input_label, file_layout)
        
        self.cs_self_contained = QCheckBox()
        self.cs_self_contained.setChecked(True)
        self.cs_single_file = QCheckBox()
        self.cs_single_file.setChecked(True)
        self.cs_trim = QCheckBox()
        
        layout.addRow("", self.cs_self_contained)
        layout.addRow("", self.cs_single_file)
        layout.addRow("", self.cs_trim)
        
        widget.setLayout(layout)

    def setup_node_ui(self, widget):
        layout = QFormLayout()
        
        file_layout = QHBoxLayout()
        self.node_input = QLineEdit()
        btn = QPushButton("Browse")
        btn.clicked.connect(lambda: self.browse_file(self.node_input, "Node Files (*.js *.json)"))
        file_layout.addWidget(self.node_input)
        file_layout.addWidget(btn)
        
        self.node_input_label = QLabel()
        layout.addRow(self.node_input_label, file_layout)
        
        self.node_target_label = QLabel()
        self.node_target = QComboBox()
        self.node_target.addItems(["host", "node18-win-x64", "node16-win-x64", "node14-win-x64"])
        layout.addRow(self.node_target_label, self.node_target)
        
        widget.setLayout(layout)

    def setup_java_ui(self, widget):
        layout = QFormLayout()
        
        file_layout = QHBoxLayout()
        self.java_input = QLineEdit()
        btn = QPushButton("Browse")
        btn.clicked.connect(lambda: self.browse_file(self.java_input, "Java JAR (*.jar)"))
        file_layout.addWidget(self.java_input)
        file_layout.addWidget(btn)
        
        self.java_input_label = QLabel()
        layout.addRow(self.java_input_label, file_layout)
        
        self.java_main_label = QLabel()
        self.java_main = QLineEdit()
        layout.addRow(self.java_main_label, self.java_main)
        
        self.java_type_label = QLabel()
        self.java_type = QComboBox()
        self.java_type.addItems(["app-image", "exe", "msi"])
        layout.addRow(self.java_type_label, self.java_type)
        
        widget.setLayout(layout)

    # --- Logic ---

    def toggle_language(self):
        self.current_lang = 'en' if self.current_lang == 'zh' else 'zh'
        self.update_ui_text()

    def update_ui_text(self):
        self.setWindowTitle(self.tr('window_title'))
        self.lang_btn.setText(self.tr('lang_switch_btn'))
        
        self.general_group.setTitle(self.tr('group_general'))
        self.label_lang.setText(self.tr('label_target_lang'))
        self.config_group.setTitle(self.tr('group_config'))
        
        self.build_btn.setText(self.tr('btn_build'))
        self.log_output.setPlaceholderText(self.tr('log_placeholder'))
        
        # Python
        self.py_input_label.setText(self.tr('py_input_label'))
        self.py_input.setPlaceholderText(self.tr('py_input_ph'))
        self.py_entry_label.setText(self.tr('py_entry_label'))
        self.py_backend_label.setText(self.tr('py_backend_label'))
        self.py_onefile.setText(self.tr('py_onefile'))
        self.py_noconsole.setText(self.tr('py_noconsole'))
        self.py_clean.setText(self.tr('py_clean'))
        
        # C#
        self.cs_input_label.setText(self.tr('cs_input_label'))
        self.cs_input.setPlaceholderText(self.tr('cs_input_ph'))
        self.cs_self_contained.setText(self.tr('cs_self_contained'))
        self.cs_single_file.setText(self.tr('cs_single_file'))
        self.cs_trim.setText(self.tr('cs_trim'))
        
        # Node
        self.node_input_label.setText(self.tr('node_input_label'))
        self.node_input.setPlaceholderText(self.tr('node_input_ph'))
        self.node_target_label.setText(self.tr('node_target_label'))
        
        # Java
        self.java_input_label.setText(self.tr('java_input_label'))
        self.java_input.setPlaceholderText(self.tr('java_input_ph'))
        self.java_main_label.setText(self.tr('java_main_class'))
        self.java_type_label.setText(self.tr('java_type_label'))

    def on_lang_changed(self, index):
        self.stack.setCurrentIndex(index)

    def browse_file(self, input_widget, filter_str):
        filename, _ = QFileDialog.getOpenFileName(self, "Select File", "", filter_str)
        if filename:
            input_widget.setText(filename)

    def browse_folder(self, input_widget):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            input_widget.setText(folder)

    def scan_python_entry(self, path):
        if not path or not os.path.exists(path):
            return
        
        self.py_entry.clear()
        if os.path.isfile(path):
            self.py_entry.addItem(path, path)
            return
            
        # Is folder
        candidates = []
        try:
            for f in os.listdir(path):
                if f.endswith(".py"):
                    candidates.append(os.path.join(path, f))
        except:
            pass
            
        if not candidates:
            return
            
        # Heuristic
        priority = ['main.py', 'app.py', 'gui.py', 'start.py']
        best = candidates[0]
        for c in candidates:
            self.py_entry.addItem(c, c)
            if os.path.basename(c).lower() in priority:
                best = c
        self.py_entry.setCurrentText(best)

    def check_tool(self, cmd_name):
        return shutil.which(cmd_name) is not None

    def start_build(self):
        idx = self.lang_combo.currentIndex()
        
        try:
            if idx == 0: # Python
                self.build_python()
            elif idx == 1: # C#
                self.build_csharp()
            elif idx == 2: # Node
                self.build_node()
            elif idx == 3: # Java
                self.build_java()
        except Exception as e:
            QMessageBox.critical(self, self.tr('err_title'), str(e))

    def build_python(self):
        entry = self.py_entry.currentText()
        if not entry:
            entry = self.py_input.text()
            
        if not entry or not os.path.exists(entry):
            raise Exception(self.tr('err_no_input'))

        project_dir = os.path.dirname(entry)
        backend_idx = self.py_backend.currentIndex()

        if backend_idx == 1: # Nuitka
            # Check for Windows Store Python
            if "WindowsApps" in sys.executable:
                raise Exception(self.tr('err_store_python'))

            # Nuitka Build Logic
            cmd = [sys.executable, "-m", "nuitka", "--follow-imports", "--assume-yes-for-downloads", "--show-scons"]
            
            if self.py_onefile.isChecked():
                cmd.append("--onefile")
            else:
                cmd.append("--standalone")
                
            if self.py_noconsole.isChecked():
                cmd.append("--windows-disable-console")
                
            if self.py_clean.isChecked():
                cmd.append("--remove-output")
                
            # Output directory
            cmd.append(f"--output-dir={os.path.join(project_dir, 'dist')}")
            
            cmd.append(entry)
            
        else: # PyInstaller
            if getattr(sys, 'frozen', False):
                # If frozen (running as exe), use global 'pyinstaller' command
                cmd = ["pyinstaller", entry]
            else:
                # If running from source, use the current python interpreter
                cmd = [sys.executable, "-m", "PyInstaller", entry]

            if self.py_onefile.isChecked(): cmd.append("--onefile")
            if self.py_noconsole.isChecked(): cmd.append("--noconsole")
            if self.py_clean.isChecked(): cmd.append("--clean")
            
            dist = os.path.join(project_dir, "dist")
            work = os.path.join(project_dir, "build")
            cmd.append(f"--distpath={dist}")
            cmd.append(f"--workpath={work}")
            cmd.append(f"--specpath={project_dir}")
        
        self.run_process(cmd, project_dir)

    def build_csharp(self):
        if not self.check_tool("dotnet"):
            raise Exception(self.tr('err_tool_missing').format("dotnet"))
            
        proj = self.cs_input.text()
        if not proj or not os.path.exists(proj):
            raise Exception(self.tr('err_no_input'))
            
        project_dir = os.path.dirname(proj)
        
        # dotnet publish -c Release -r win-x64 ...
        cmd = ["dotnet", "publish", proj, "-c", "Release", "-r", "win-x64"]
        
        if self.cs_self_contained.isChecked():
            cmd.append("--self-contained")
            cmd.append("true")
        else:
            cmd.append("--self-contained")
            cmd.append("false")
            
        if self.cs_single_file.isChecked():
            cmd.append("-p:PublishSingleFile=true")
            
        if self.cs_trim.isChecked():
            cmd.append("-p:PublishTrimmed=true")
            
        output_dir = os.path.join(project_dir, "dist")
        cmd.append(f"--output={output_dir}")
        
        self.run_process(cmd, project_dir)

    def build_node(self):
        # Requires 'pkg' installed globally: npm install -g pkg
        # Or we can use npx pkg
        if not self.check_tool("npx"):
            if not self.check_tool("npm"):
                raise Exception(self.tr('err_tool_missing').format("Node.js (npm/npx)"))
        
        inp = self.node_input.text()
        if not inp or not os.path.exists(inp):
            raise Exception(self.tr('err_no_input'))
            
        project_dir = os.path.dirname(inp)
        target_ver = self.node_target.currentText()
        
        cmd = ["npx.cmd" if os.name == 'nt' else "npx", "pkg", inp, "--targets", target_ver, "--out-path", "dist"]
        
        self.run_process(cmd, project_dir)

    def build_java(self):
        if not self.check_tool("jpackage"):
            raise Exception(self.tr('err_tool_missing').format("JDK (jpackage)"))
            
        jar = self.java_input.text()
        if not jar or not os.path.exists(jar):
            raise Exception(self.tr('err_no_input'))
            
        project_dir = os.path.dirname(jar)
        jar_name = os.path.basename(jar)
        name_no_ext = os.path.splitext(jar_name)[0]
        
        # jpackage --input . --main-jar app.jar --name MyApp
        cmd = ["jpackage", "--input", project_dir, "--main-jar", jar_name, "--name", name_no_ext]
        
        if self.java_main.text().strip():
            cmd.append(f"--main-class={self.java_main.text().strip()}")
            
        cmd.append(f"--type={self.java_type.currentText()}")
        cmd.append(f"--dest={os.path.join(project_dir, 'dist')}")
        
        self.run_process(cmd, project_dir)

    def run_process(self, cmd, cwd):
        self.log_output.clear()
        self.log_output.append(f"Starting Build Process...\n")
        self.log_output.append(f"Command: {' '.join(cmd)}\n")
        self.log_output.append("-" * 50)
        
        self.build_btn.setEnabled(False)
        self.process.setWorkingDirectory(cwd)
        self.process.start(cmd[0], cmd[1:])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8", errors="ignore")
        self.log_output.append(stdout)
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8", errors="ignore")
        self.log_output.append(stderr)
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def process_finished(self):
        self.build_btn.setEnabled(True)
        if self.process.exitCode() == 0:
            self.log_output.append(f"\n{self.tr('msg_success')}")
            QMessageBox.information(self, self.tr('window_title'), self.tr('msg_success'))
        else:
            self.log_output.append(f"\n{self.tr('msg_fail')}")
            QMessageBox.critical(self, self.tr('err_title'), self.tr('msg_fail'))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultiPackagerApp()
    window.show()
    sys.exit(app.exec())

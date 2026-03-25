import os
import json
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QFileDialog, 
                               QCheckBox, QTextEdit, QGroupBox, QMessageBox, 
                               QComboBox, QStackedWidget, QFormLayout)
from PySide6.QtCore import QProcess, Qt

from src.core.builders import Builder
from src.core.config import PythonConfig, CSharpConfig, NodeConfig, JavaConfig
from src.core.utils import get_resource_path

class MultiPackagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = 'zh'
        self.languages = ['Python', 'C# (.NET)', 'Node.js (JS)', 'Java']
        
        # Load Translations
        self.load_translations()
        
        self.init_ui()
        self.update_ui_text()

    def load_translations(self):
        try:
            path = get_resource_path("translations.json")
            with open(path, 'r', encoding='utf-8') as f:
                self.trans_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load translations: {e}")
            self.trans_data = {'en': {}, 'zh': {}}

    def tr(self, key):
        return self.trans_data.get(self.current_lang, {}).get(key, key)

    def init_ui(self):
        self.resize(850, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Top Bar ---
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.lang_btn = QPushButton()
        self.lang_btn.setFixedWidth(120)
        self.lang_btn.clicked.connect(self.toggle_language)
        top_bar.addWidget(self.lang_btn)
        main_layout.addLayout(top_bar)

        # --- General Settings ---
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

        # --- Configuration Stack ---
        self.config_group = QGroupBox()
        config_layout = QVBoxLayout()
        self.stack = QStackedWidget()
        
        self.page_py = QWidget()
        self.setup_python_ui(self.page_py)
        self.stack.addWidget(self.page_py)
        
        self.page_cs = QWidget()
        self.setup_csharp_ui(self.page_cs)
        self.stack.addWidget(self.page_cs)
        
        self.page_node = QWidget()
        self.setup_node_ui(self.page_node)
        self.stack.addWidget(self.page_node)
        
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

    def setup_python_ui(self, widget):
        layout = QFormLayout() 
        
        # File/Folder
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

        # Backend
        self.py_backend = QComboBox()
        self.py_backend.addItems(["PyInstaller", "Nuitka"])
        self.py_backend_label = QLabel()
        layout.addRow(self.py_backend_label, self.py_backend)
        
        # Interpreter (New Feature)
        self.py_interpreter_label = QLabel()
        self.py_interpreter = QLineEdit()
        self.py_interpreter.setPlaceholderText("Auto-detect")
        btn_interp = QPushButton("...")
        btn_interp.setFixedWidth(40)
        btn_interp.clicked.connect(lambda: self.browse_file(self.py_interpreter, "Python Executable (python.exe)"))
        
        interp_layout = QHBoxLayout()
        interp_layout.addWidget(self.py_interpreter)
        interp_layout.addWidget(btn_interp)
        layout.addRow(self.py_interpreter_label, interp_layout)
        
        # Options
        self.py_onefile = QCheckBox()
        self.py_onefile.setChecked(True)
        self.py_noconsole = QCheckBox()
        self.py_clean = QCheckBox()
        self.py_clean.setChecked(True)
        
        layout.addRow("", self.py_onefile)
        layout.addRow("", self.py_noconsole)
        layout.addRow("", self.py_clean)
        
        widget.setLayout(layout)
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
        
        # RID (New Feature)
        self.cs_rid_label = QLabel()
        self.cs_rid = QComboBox()
        self.cs_rid.addItems(["win-x64", "win-x86", "win-arm64", "linux-x64", "osx-x64", "osx-arm64"])
        self.cs_rid.setEditable(True)
        layout.addRow(self.cs_rid_label, self.cs_rid)
        
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
        self.node_target.addItems(["host", "node18-win-x64", "node16-win-x64", "node14-win-x64", "node18-linux-x64", "node18-macos-x64"])
        self.node_target.setEditable(True)
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
        self.java_type.addItems(["exe", "msi", "app-image"])
        layout.addRow(self.java_type_label, self.java_type)
        
        widget.setLayout(layout)

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
        self.py_interpreter_label.setText(self.tr('py_interpreter_label'))
        self.py_interpreter.setPlaceholderText(self.tr('py_interpreter_ph'))
        self.py_onefile.setText(self.tr('py_onefile'))
        self.py_noconsole.setText(self.tr('py_noconsole'))
        self.py_clean.setText(self.tr('py_clean'))
        
        # C#
        self.cs_input_label.setText(self.tr('cs_input_label'))
        self.cs_input.setPlaceholderText(self.tr('cs_input_ph'))
        self.cs_rid_label.setText(self.tr('cs_rid_label'))
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

    def browse_file(self, widget, filter_str):
        f, _ = QFileDialog.getOpenFileName(self, "Select", "", filter_str)
        if f: widget.setText(f)

    def browse_folder(self, widget):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d: widget.setText(d)

    def scan_python_entry(self, path):
        if not path or not os.path.exists(path): return
        self.py_entry.clear()
        if os.path.isfile(path):
            self.py_entry.addItem(path)
            return
        
        # Scan folder
        candidates = []
        try:
            for f in os.listdir(path):
                if f.endswith(".py"): candidates.append(os.path.join(path, f))
        except: pass
        
        priority = ['main.py', 'app.py', 'gui.py', 'start.py']
        best = candidates[0] if candidates else ""
        for c in candidates:
            self.py_entry.addItem(c)
            if os.path.basename(c).lower() in priority: best = c
        if best: self.py_entry.setCurrentText(best)

    def start_build(self):
        idx = self.lang_combo.currentIndex()
        cmd, cwd = None, None
        
        try:
            if idx == 0: # Python
                config = PythonConfig(
                    entry=self.py_entry.currentText() or self.py_input.text(),
                    backend='nuitka' if self.py_backend.currentIndex() == 1 else 'pyinstaller',
                    onefile=self.py_onefile.isChecked(),
                    noconsole=self.py_noconsole.isChecked(),
                    clean=self.py_clean.isChecked(),
                    interpreter=self.py_interpreter.text().strip()
                )
                cmd, cwd = Builder.build_python(config)
                
            elif idx == 1: # C#
                config = CSharpConfig(
                    project_path=self.cs_input.text(),
                    rid=self.cs_rid.currentText(),
                    self_contained=self.cs_self_contained.isChecked(),
                    single_file=self.cs_single_file.isChecked(),
                    trim=self.cs_trim.isChecked()
                )
                cmd, cwd = Builder.build_csharp(config)
                
            elif idx == 2: # Node
                config = NodeConfig(
                    entry=self.node_input.text(),
                    target=self.node_target.currentText()
                )
                cmd, cwd = Builder.build_node(config)
                
            elif idx == 3: # Java
                path = self.java_input.text()
                config = JavaConfig(
                    input_path=os.path.dirname(path) if path else "",
                    main_jar=os.path.basename(path) if path else "",
                    main_class=self.java_main.text().strip(),
                    output_type=self.java_type.currentText()
                )
                cmd, cwd = Builder.build_java(config)
                
            self.run_process(cmd, cwd)
            
        except Exception as e:
            QMessageBox.critical(self, self.tr('err_title'), str(e))

    def run_process(self, cmd, cwd):
        self.log_output.clear()
        self.log_output.append(f"Starting Build...\nCMD: {' '.join(cmd)}\nCWD: {cwd}\n" + "-"*40 + "\n")
        self.build_btn.setEnabled(False)
        self.process.setWorkingDirectory(cwd)
        self.process.start(cmd[0], cmd[1:])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        self.log_output.append(bytes(data).decode('utf8', errors='ignore'))
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        self.log_output.append(bytes(data).decode('utf8', errors='ignore'))
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def process_finished(self):
        self.build_btn.setEnabled(True)
        if self.process.exitCode() == 0:
            self.log_output.append(f"\n{self.tr('msg_success')}")
            QMessageBox.information(self, "Success", self.tr('msg_success'))
        else:
            self.log_output.append(f"\n{self.tr('msg_fail')}")
            QMessageBox.critical(self, "Failed", self.tr('msg_fail'))

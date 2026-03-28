import json
import os
import re

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.builders import Builder
from src.core.config import AndroidConfig, CSharpConfig, JavaConfig, NodeConfig, PythonConfig
from src.core.utils import get_resource_path


class MultiPackagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = "zh"
        self.target_items = {
            "en": ["Python", "C# (.NET)", "Node.js (JS)", "Java", "Android (Web Folder)"],
            "zh": ["Python", "C# (.NET)", "Node.js (JS)", "Java", "Android（网页文件夹）"],
        }
        self.android_name_auto = True
        self.android_output_auto = True
        self.android_package_auto = True
        self.current_success_message = ""
        self.current_failure_message = ""

        self.load_translations()
        self.init_ui()
        self.update_ui_text()

    def load_translations(self):
        try:
            path = get_resource_path("translations.json")
            with open(path, "r", encoding="utf-8") as file_obj:
                self.trans_data = json.load(file_obj)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to load translations: {exc}")
            self.trans_data = {"en": {}, "zh": {}}

    def tr(self, key):
        return self.trans_data.get(self.current_lang, {}).get(key, key)

    def init_ui(self):
        self.resize(980, 760)
        self.setMinimumSize(860, 660)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.lang_btn = QPushButton()
        self.lang_btn.setFixedWidth(140)
        self.lang_btn.clicked.connect(self.toggle_language)
        top_bar.addWidget(self.lang_btn)
        main_layout.addLayout(top_bar)

        self.general_group = QGroupBox()
        general_layout = QHBoxLayout()
        self.label_lang = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.target_items[self.current_lang])
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        general_layout.addWidget(self.label_lang)
        general_layout.addWidget(self.lang_combo)
        general_layout.addStretch()
        self.general_group.setLayout(general_layout)
        main_layout.addWidget(self.general_group)

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

        self.page_android = QWidget()
        self.setup_android_ui(self.page_android)
        self.stack.addWidget(self.page_android)

        config_layout.addWidget(self.stack)
        self.config_group.setLayout(config_layout)
        main_layout.addWidget(self.config_group)

        self.build_btn = QPushButton()
        self.build_btn.setStyleSheet(
            "font-weight: bold; font-size: 14px; padding: 10px; "
            "background-color: #2E8B57; color: white; border-radius: 4px;"
        )
        self.build_btn.clicked.connect(self.start_build)
        main_layout.addWidget(self.build_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 12px; "
            "background-color: #1E1E1E; color: #D4D4D4;"
        )
        main_layout.addWidget(self.log_output)

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

    def setup_python_ui(self, widget):
        layout = QFormLayout()

        file_layout = QHBoxLayout()
        self.py_input = QLineEdit()
        self.py_file_btn = QPushButton()
        self.py_file_btn.clicked.connect(lambda: self.browse_file(self.py_input, "Python Files (*.py)"))
        self.py_folder_btn = QPushButton()
        self.py_folder_btn.clicked.connect(lambda: self.browse_folder(self.py_input))
        file_layout.addWidget(self.py_input)
        file_layout.addWidget(self.py_file_btn)
        file_layout.addWidget(self.py_folder_btn)
        self.py_input_label = QLabel()
        layout.addRow(self.py_input_label, file_layout)

        self.py_entry = QComboBox()
        self.py_entry.setEditable(True)
        self.py_entry_label = QLabel()
        layout.addRow(self.py_entry_label, self.py_entry)

        self.py_backend = QComboBox()
        self.py_backend.addItems(["PyInstaller", "Nuitka"])
        self.py_backend_label = QLabel()
        layout.addRow(self.py_backend_label, self.py_backend)

        self.py_interpreter_label = QLabel()
        self.py_interpreter = QLineEdit()
        self.py_interp_btn = QPushButton("...")
        self.py_interp_btn.setFixedWidth(40)
        self.py_interp_btn.clicked.connect(
            lambda: self.browse_file(self.py_interpreter, "Python Executable (python.exe)")
        )
        interp_layout = QHBoxLayout()
        interp_layout.addWidget(self.py_interpreter)
        interp_layout.addWidget(self.py_interp_btn)
        layout.addRow(self.py_interpreter_label, interp_layout)

        self.py_onefile = QCheckBox()
        self.py_onefile.setChecked(True)
        self.py_noconsole = QCheckBox()
        self.py_clean = QCheckBox()
        self.py_clean.setChecked(True)

        layout.addRow("", self.py_onefile)
        layout.addRow("", self.py_noconsole)
        layout.addRow("", self.py_clean)

        widget.setLayout(layout)
        self.py_input.textChanged.connect(self.scan_python_entry)

    def setup_csharp_ui(self, widget):
        layout = QFormLayout()

        file_layout = QHBoxLayout()
        self.cs_input = QLineEdit()
        self.cs_browse_btn = QPushButton()
        self.cs_browse_btn.clicked.connect(lambda: self.browse_file(self.cs_input, "C# Project (*.csproj)"))
        file_layout.addWidget(self.cs_input)
        file_layout.addWidget(self.cs_browse_btn)
        self.cs_input_label = QLabel()
        layout.addRow(self.cs_input_label, file_layout)

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
        self.node_browse_btn = QPushButton()
        self.node_browse_btn.clicked.connect(lambda: self.browse_file(self.node_input, "Node Files (*.js *.json)"))
        file_layout.addWidget(self.node_input)
        file_layout.addWidget(self.node_browse_btn)
        self.node_input_label = QLabel()
        layout.addRow(self.node_input_label, file_layout)

        self.node_target_label = QLabel()
        self.node_target = QComboBox()
        self.node_target.addItems(
            ["host", "node18-win-x64", "node16-win-x64", "node14-win-x64", "node18-linux-x64", "node18-macos-x64"]
        )
        self.node_target.setEditable(True)
        layout.addRow(self.node_target_label, self.node_target)

        widget.setLayout(layout)

    def setup_java_ui(self, widget):
        layout = QFormLayout()

        file_layout = QHBoxLayout()
        self.java_input = QLineEdit()
        self.java_browse_btn = QPushButton()
        self.java_browse_btn.clicked.connect(lambda: self.browse_file(self.java_input, "Java JAR (*.jar)"))
        file_layout.addWidget(self.java_input)
        file_layout.addWidget(self.java_browse_btn)
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

    def setup_android_ui(self, widget):
        layout = QFormLayout()

        source_layout = QHBoxLayout()
        self.android_source = QLineEdit()
        self.android_source_btn = QPushButton()
        self.android_source_btn.clicked.connect(self.browse_android_source)
        source_layout.addWidget(self.android_source)
        source_layout.addWidget(self.android_source_btn)
        self.android_source_label = QLabel()
        layout.addRow(self.android_source_label, source_layout)

        self.android_entry = QComboBox()
        self.android_entry.setEditable(True)
        self.android_entry_label = QLabel()
        layout.addRow(self.android_entry_label, self.android_entry)

        output_layout = QHBoxLayout()
        self.android_output = QLineEdit()
        self.android_output_btn = QPushButton()
        self.android_output_btn.clicked.connect(self.browse_android_output)
        output_layout.addWidget(self.android_output)
        output_layout.addWidget(self.android_output_btn)
        self.android_output_label = QLabel()
        layout.addRow(self.android_output_label, output_layout)

        self.android_app_name_label = QLabel()
        self.android_app_name = QLineEdit()
        layout.addRow(self.android_app_name_label, self.android_app_name)

        self.android_package_label = QLabel()
        self.android_package = QLineEdit()
        layout.addRow(self.android_package_label, self.android_package)

        self.android_min_sdk_label = QLabel()
        self.android_min_sdk = QSpinBox()
        self.android_min_sdk.setRange(21, 40)
        self.android_min_sdk.setValue(24)
        layout.addRow(self.android_min_sdk_label, self.android_min_sdk)

        self.android_target_sdk_label = QLabel()
        self.android_target_sdk = QSpinBox()
        self.android_target_sdk.setRange(21, 40)
        self.android_target_sdk.setValue(35)
        layout.addRow(self.android_target_sdk_label, self.android_target_sdk)

        self.android_build_mode_label = QLabel()
        self.android_build_mode = QComboBox()
        layout.addRow(self.android_build_mode_label, self.android_build_mode)

        gradle_layout = QHBoxLayout()
        self.android_gradle = QLineEdit()
        self.android_gradle_btn = QPushButton()
        self.android_gradle_btn.clicked.connect(self.browse_android_gradle)
        gradle_layout.addWidget(self.android_gradle)
        gradle_layout.addWidget(self.android_gradle_btn)
        self.android_gradle_label = QLabel()
        layout.addRow(self.android_gradle_label, gradle_layout)

        sdk_layout = QHBoxLayout()
        self.android_sdk = QLineEdit()
        self.android_sdk_btn = QPushButton()
        self.android_sdk_btn.clicked.connect(self.browse_android_sdk)
        sdk_layout.addWidget(self.android_sdk)
        sdk_layout.addWidget(self.android_sdk_btn)
        self.android_sdk_label = QLabel()
        layout.addRow(self.android_sdk_label, sdk_layout)

        self.android_mobile_adapt = QCheckBox()
        self.android_mobile_adapt.setChecked(True)
        layout.addRow("", self.android_mobile_adapt)

        self.android_hint = QLabel()
        self.android_hint.setWordWrap(True)
        self.android_hint.setStyleSheet("color: #777777;")
        layout.addRow("", self.android_hint)

        widget.setLayout(layout)

        self.android_source.textChanged.connect(self.scan_android_folder)
        self.android_app_name.textChanged.connect(self.on_android_app_name_changed)
        self.android_app_name.textEdited.connect(self.mark_android_name_manual)
        self.android_output.textEdited.connect(self.mark_android_output_manual)
        self.android_package.textEdited.connect(self.mark_android_package_manual)
        self.android_build_mode.currentIndexChanged.connect(self.update_android_build_fields)

    def toggle_language(self):
        self.current_lang = "en" if self.current_lang == "zh" else "zh"
        self.update_ui_text()

    def update_ui_text(self):
        self.setWindowTitle(self.tr("window_title"))
        self.lang_btn.setText(self.tr("lang_switch_btn"))
        self.general_group.setTitle(self.tr("group_general"))
        self.label_lang.setText(self.tr("label_target_lang"))
        self.config_group.setTitle(self.tr("group_config"))
        self.build_btn.setText(self.tr("btn_build"))
        self.log_output.setPlaceholderText(self.tr("log_placeholder"))

        current_index = self.lang_combo.currentIndex()
        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()
        self.lang_combo.addItems(self.target_items[self.current_lang])
        self.lang_combo.setCurrentIndex(max(current_index, 0))
        self.lang_combo.blockSignals(False)

        self.py_input_label.setText(self.tr("py_input_label"))
        self.py_input.setPlaceholderText(self.tr("py_input_ph"))
        self.py_entry_label.setText(self.tr("py_entry_label"))
        self.py_backend_label.setText(self.tr("py_backend_label"))
        self.py_interpreter_label.setText(self.tr("py_interpreter_label"))
        self.py_interpreter.setPlaceholderText(self.tr("py_interpreter_ph"))
        self.py_onefile.setText(self.tr("py_onefile"))
        self.py_noconsole.setText(self.tr("py_noconsole"))
        self.py_clean.setText(self.tr("py_clean"))
        self.py_file_btn.setText(self.tr("btn_file_short"))
        self.py_folder_btn.setText(self.tr("btn_folder_short"))

        self.cs_input_label.setText(self.tr("cs_input_label"))
        self.cs_input.setPlaceholderText(self.tr("cs_input_ph"))
        self.cs_rid_label.setText(self.tr("cs_rid_label"))
        self.cs_self_contained.setText(self.tr("cs_self_contained"))
        self.cs_single_file.setText(self.tr("cs_single_file"))
        self.cs_trim.setText(self.tr("cs_trim"))
        self.cs_browse_btn.setText(self.tr("btn_browse_file"))

        self.node_input_label.setText(self.tr("node_input_label"))
        self.node_input.setPlaceholderText(self.tr("node_input_ph"))
        self.node_target_label.setText(self.tr("node_target_label"))
        self.node_browse_btn.setText(self.tr("btn_browse_file"))

        self.java_input_label.setText(self.tr("java_input_label"))
        self.java_input.setPlaceholderText(self.tr("java_input_ph"))
        self.java_main_label.setText(self.tr("java_main_class"))
        self.java_type_label.setText(self.tr("java_type_label"))
        self.java_browse_btn.setText(self.tr("btn_browse_file"))

        self.android_source_label.setText(self.tr("android_source_label"))
        self.android_source.setPlaceholderText(self.tr("android_source_ph"))
        self.android_entry_label.setText(self.tr("android_entry_label"))
        self.set_combo_placeholder(self.android_entry, self.tr("android_entry_ph"))
        self.android_output_label.setText(self.tr("android_output_label"))
        self.android_output.setPlaceholderText(self.tr("android_output_ph"))
        self.android_app_name_label.setText(self.tr("android_app_name_label"))
        self.android_app_name.setPlaceholderText(self.tr("android_app_name_ph"))
        self.android_package_label.setText(self.tr("android_package_label"))
        self.android_package.setPlaceholderText(self.tr("android_package_ph"))
        self.android_min_sdk_label.setText(self.tr("android_min_sdk_label"))
        self.android_target_sdk_label.setText(self.tr("android_target_sdk_label"))
        self.android_build_mode_label.setText(self.tr("android_build_mode_label"))
        self.set_android_build_modes()
        self.android_gradle_label.setText(self.tr("android_gradle_label"))
        self.android_gradle.setPlaceholderText(self.tr("android_gradle_ph"))
        self.android_sdk_label.setText(self.tr("android_sdk_label"))
        self.android_sdk.setPlaceholderText(self.tr("android_sdk_ph"))
        self.android_mobile_adapt.setText(self.tr("android_mobile_adapt"))
        self.android_hint.setText(self.tr("android_hint"))
        self.android_source_btn.setText(self.tr("btn_browse_folder"))
        self.android_output_btn.setText(self.tr("btn_browse_folder"))
        self.android_gradle_btn.setText(self.tr("btn_browse_file"))
        self.android_sdk_btn.setText(self.tr("btn_browse_folder"))

    def set_combo_placeholder(self, combo, text):
        if combo.isEditable() and combo.lineEdit():
            combo.lineEdit().setPlaceholderText(text)

    def set_android_build_modes(self):
        current_mode = self.android_build_mode.currentData()
        options = [
            ("project", self.tr("android_build_mode_project")),
            ("apk_debug", self.tr("android_build_mode_apk_debug")),
            ("apk_release", self.tr("android_build_mode_apk_release")),
            ("aab_release", self.tr("android_build_mode_aab_release")),
        ]

        self.android_build_mode.blockSignals(True)
        self.android_build_mode.clear()
        selected_index = 0
        for index, (value, label) in enumerate(options):
            self.android_build_mode.addItem(label, value)
            if value == current_mode:
                selected_index = index
        self.android_build_mode.setCurrentIndex(selected_index)
        self.android_build_mode.blockSignals(False)
        self.update_android_build_fields()

    def update_android_build_fields(self, _index=None):
        build_mode = self.android_build_mode.currentData() or "project"
        needs_gradle = build_mode != "project"
        self.android_gradle.setEnabled(needs_gradle)
        self.android_gradle_btn.setEnabled(needs_gradle)
        self.android_sdk.setEnabled(needs_gradle)
        self.android_sdk_btn.setEnabled(needs_gradle)

    def on_lang_changed(self, index):
        self.stack.setCurrentIndex(index)

    def browse_file(self, widget, filter_str):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("dialog_select"), "", filter_str)
        if path:
            widget.setText(path)

    def browse_folder(self, widget):
        directory = QFileDialog.getExistingDirectory(self, self.tr("dialog_select"))
        if directory:
            widget.setText(directory)

    def browse_android_source(self):
        directory = QFileDialog.getExistingDirectory(self, self.tr("dialog_select"))
        if directory:
            self.android_source.setText(directory)

    def browse_android_output(self):
        directory = QFileDialog.getExistingDirectory(self, self.tr("dialog_select"))
        if directory:
            source_path = self.android_source.text().strip()
            folder_name = self.default_android_output_name(source_path)
            self.android_output.setText(os.path.join(directory, folder_name))
            self.android_output_auto = False

    def browse_android_gradle(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("dialog_select"),
            "",
            "Gradle Executable (gradlew* gradle*);;All Files (*)",
        )
        if path:
            self.android_gradle.setText(path)

    def browse_android_sdk(self):
        directory = QFileDialog.getExistingDirectory(self, self.tr("dialog_select"))
        if directory:
            self.android_sdk.setText(directory)

    def scan_python_entry(self, path):
        if not path or not os.path.exists(path):
            return

        self.py_entry.clear()
        if os.path.isfile(path):
            self.py_entry.addItem(path)
            return

        candidates = []
        try:
            for file_name in os.listdir(path):
                if file_name.endswith(".py"):
                    candidates.append(os.path.join(path, file_name))
        except OSError:
            return

        priority = ["main.py", "app.py", "gui.py", "start.py"]
        best = candidates[0] if candidates else ""
        for candidate in candidates:
            self.py_entry.addItem(candidate)
            if os.path.basename(candidate).lower() in priority:
                best = candidate
        if best:
            self.py_entry.setCurrentText(best)

    def scan_android_folder(self, path):
        self.android_entry.clear()
        if not path or not os.path.isdir(path):
            return

        html_files = []
        ignored_dirs = {".git", ".gradle", ".idea", "__pycache__", "node_modules"}
        for root, dirs, files in os.walk(path):
            dirs[:] = [directory for directory in dirs if directory not in ignored_dirs]
            for file_name in files:
                if file_name.lower().endswith((".html", ".htm")):
                    full_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(full_path, path).replace("\\", "/")
                    html_files.append(rel_path)

        html_files.sort(key=self.android_entry_sort_key)
        for rel_path in html_files:
            self.android_entry.addItem(rel_path)
        if html_files:
            self.android_entry.setCurrentText(html_files[0])

        if self.android_name_auto or not self.android_app_name.text().strip():
            self.android_app_name.setText(self.make_android_app_name(path))
            self.android_name_auto = True

        if self.android_output_auto or not self.android_output.text().strip():
            parent_dir = os.path.dirname(os.path.abspath(path))
            self.android_output.setText(os.path.join(parent_dir, self.default_android_output_name(path)))
            self.android_output_auto = True

        if self.android_package_auto or not self.android_package.text().strip():
            self.android_package.setText(self.make_android_package_name(self.android_app_name.text()))
            self.android_package_auto = True

    def android_entry_sort_key(self, rel_path):
        name = os.path.basename(rel_path).lower()
        priority = ["index.html", "main.html", "home.html", "default.html"]
        rank = priority.index(name) if name in priority else len(priority)
        return rank, rel_path.count("/"), rel_path.lower()

    def make_android_app_name(self, source_path):
        base_name = os.path.basename(os.path.normpath(source_path))
        parts = re.split(r"[_\-\s]+", base_name)
        pretty_name = " ".join(part.capitalize() for part in parts if part)
        return pretty_name or "Compass Android App"

    def make_android_package_name(self, app_name):
        app_slug = re.sub(r"[^a-z0-9]+", "", app_name.lower()) or "app"
        return f"com.compass.{app_slug}"

    def default_android_output_name(self, source_path):
        base_name = os.path.basename(os.path.normpath(source_path)) if source_path else "webapp"
        return f"{base_name}-android-project"

    def on_android_app_name_changed(self, _text):
        if self.android_package_auto:
            self.android_package.setText(self.make_android_package_name(self.android_app_name.text()))

    def mark_android_name_manual(self, _text):
        self.android_name_auto = False

    def mark_android_output_manual(self, _text):
        self.android_output_auto = False

    def mark_android_package_manual(self, _text):
        self.android_package_auto = False

    def start_build(self):
        idx = self.lang_combo.currentIndex()
        cmd, cwd = None, None

        try:
            if idx == 0:
                config = PythonConfig(
                    entry=self.py_entry.currentText() or self.py_input.text(),
                    backend="nuitka" if self.py_backend.currentIndex() == 1 else "pyinstaller",
                    onefile=self.py_onefile.isChecked(),
                    noconsole=self.py_noconsole.isChecked(),
                    clean=self.py_clean.isChecked(),
                    interpreter=self.py_interpreter.text().strip(),
                )
                cmd, cwd = Builder.build_python(config)

            elif idx == 1:
                config = CSharpConfig(
                    project_path=self.cs_input.text(),
                    rid=self.cs_rid.currentText(),
                    self_contained=self.cs_self_contained.isChecked(),
                    single_file=self.cs_single_file.isChecked(),
                    trim=self.cs_trim.isChecked(),
                )
                cmd, cwd = Builder.build_csharp(config)

            elif idx == 2:
                config = NodeConfig(entry=self.node_input.text(), target=self.node_target.currentText())
                cmd, cwd = Builder.build_node(config)

            elif idx == 3:
                path = self.java_input.text()
                config = JavaConfig(
                    input_path=os.path.dirname(path) if path else "",
                    main_jar=os.path.basename(path) if path else "",
                    main_class=self.java_main.text().strip(),
                    output_type=self.java_type.currentText(),
                )
                cmd, cwd = Builder.build_java(config)

            elif idx == 4:
                config = AndroidConfig(
                    source_dir=self.android_source.text().strip(),
                    output_dir=self.android_output.text().strip(),
                    start_page=self.android_entry.currentText().strip(),
                    app_name=self.android_app_name.text().strip(),
                    package_name=self.android_package.text().strip(),
                    min_sdk=self.android_min_sdk.value(),
                    target_sdk=self.android_target_sdk.value(),
                    mobile_adapt=self.android_mobile_adapt.isChecked(),
                    prefer_built_web_root=True,
                    build_mode=self.android_build_mode.currentData() or "project",
                    gradle_path=self.android_gradle.text().strip(),
                    android_sdk_path=self.android_sdk.text().strip(),
                )
                self.build_btn.setEnabled(False)
                QApplication.processEvents()
                result = Builder.build_android(config)
                if result["cmd"] is None:
                    self.log_output.clear()
                    self.log_output.append(result["log_text"])
                    QMessageBox.information(
                        self,
                        self.tr("msg_success_title"),
                        self.tr("android_msg_success").format(result["project_dir"]),
                    )
                    self.build_btn.setEnabled(True)
                    return

                self.run_process(
                    result["cmd"],
                    result["cwd"],
                    initial_log=result["log_text"],
                    success_message=self.tr("android_package_success").format(result["artifact_dir"]),
                    fail_message=self.tr("android_package_fail"),
                )
                return

            self.run_process(cmd, cwd)

        except Exception as exc:
            self.build_btn.setEnabled(True)
            QMessageBox.critical(self, self.tr("err_title"), str(exc))

    def run_process(self, cmd, cwd, initial_log="", success_message="", fail_message=""):
        self.log_output.clear()
        if initial_log:
            self.log_output.append(initial_log.rstrip() + "\n")
        self.log_output.append(f"Starting Build...\nCMD: {' '.join(cmd)}\nCWD: {cwd}\n" + "-" * 40 + "\n")
        self.current_success_message = success_message or self.tr("msg_success")
        self.current_failure_message = fail_message or self.tr("msg_fail")
        self.build_btn.setEnabled(False)
        self.process.setWorkingDirectory(cwd)
        self.process.start(cmd[0], cmd[1:])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        self.log_output.append(bytes(data).decode("utf8", errors="ignore"))
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        self.log_output.append(bytes(data).decode("utf8", errors="ignore"))
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def process_finished(self):
        self.build_btn.setEnabled(True)
        if self.process.exitCode() == 0:
            self.log_output.append(f"\n{self.tr('msg_success')}")
            QMessageBox.information(self, self.tr("msg_success_title"), self.current_success_message or self.tr("msg_success"))
        else:
            self.log_output.append(f"\n{self.tr('msg_fail')}")
            QMessageBox.critical(self, self.tr("msg_fail_title"), self.current_failure_message or self.tr("msg_fail"))

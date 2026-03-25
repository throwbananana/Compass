import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import AndroidConfig, PythonConfig, CSharpConfig, NodeConfig, JavaConfig
from core.builders import Builder

class TestBuilders(unittest.TestCase):
    
    @patch('os.path.exists', return_value=True)
    @patch('shutil.which', return_value='/usr/bin/python')
    def test_build_python_pyinstaller(self, mock_which, mock_exists):
        config = PythonConfig(entry="main.py", backend="pyinstaller")
        cmd, _ = Builder.build_python(config)
        self.assertIn("PyInstaller", cmd[2])
        self.assertIn("--onefile", cmd)
        
    @patch('os.path.exists', return_value=True)
    @patch('shutil.which', return_value='/usr/bin/dotnet')
    def test_build_csharp(self, mock_which, mock_exists):
        config = CSharpConfig(project_path="App.csproj", rid="linux-x64")
        cmd, _ = Builder.build_csharp(config)
        self.assertEqual(cmd[0], "dotnet")
        self.assertIn("linux-x64", cmd)
        self.assertIn("--self-contained=true", cmd)

    @patch('os.path.exists', return_value=True)
    @patch('shutil.which', return_value='/usr/bin/npx')
    def test_build_node(self, mock_which, mock_exists):
        config = NodeConfig(entry="app.js")
        cmd, _ = Builder.build_node(config)
        self.assertIn("pkg", cmd)
        self.assertIn("app.js", cmd)

    @patch('os.path.exists', return_value=True)
    @patch('shutil.which', return_value='/usr/bin/jpackage')
    def test_build_java(self, mock_which, mock_exists):
        config = JavaConfig(input_path=".", main_jar="app.jar", output_type="msi")
        cmd, _ = Builder.build_java(config)
        self.assertEqual(cmd[0], "jpackage")
        self.assertIn("--type=msi", cmd)
        self.assertIn("app.jar", cmd)

    def test_build_android_generates_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "webapp"
            output_dir = Path(temp_dir) / "android-project"
            (source_dir / "pages").mkdir(parents=True)
            (source_dir / "index.html").write_text(
                "<html><head></head><body><h1>Home</h1></body></html>",
                encoding="utf-8",
            )
            (source_dir / "pages" / "about.html").write_text(
                "<html><head></head><body><h1>About</h1></body></html>",
                encoding="utf-8",
            )

            config = AndroidConfig(
                source_dir=str(source_dir),
                output_dir=str(output_dir),
                app_name="Demo App",
                package_name="com.demo.app",
            )
            result = Builder.build_android(config)

            self.assertEqual(result["project_dir"], str(output_dir.resolve()))
            self.assertIsNone(result["cmd"])
            self.assertTrue((output_dir / "app" / "src" / "main" / "AndroidManifest.xml").exists())
            self.assertTrue((output_dir / "app" / "src" / "main" / "java" / "com" / "demo" / "app" / "MainActivity.java").exists())
            self.assertIn("Android project generated successfully.", result["log_text"])
            self.assertIn("Start Page: index.html", result["log_text"])

            root_html = (output_dir / "app" / "src" / "main" / "assets" / "app" / "index.html").read_text(encoding="utf-8")
            nested_html = (output_dir / "app" / "src" / "main" / "assets" / "app" / "pages" / "about.html").read_text(encoding="utf-8")
            self.assertIn('href="compass-mobile-adapter.css"', root_html)
            self.assertIn('src="compass-mobile-adapter.js"', root_html)
            self.assertIn('href="../compass-mobile-adapter.css"', nested_html)
            self.assertIn('src="../compass-mobile-adapter.js"', nested_html)

    def test_build_android_prepares_gradle_apk_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "webapp"
            output_dir = Path(temp_dir) / "android-project"
            sdk_dir = Path(temp_dir) / "AndroidSdk"
            gradle_dir = Path(temp_dir) / "gradle-bin"
            gradle_dir.mkdir()
            sdk_dir.mkdir()
            source_dir.mkdir()
            (source_dir / "index.html").write_text("<html><body>Hello</body></html>", encoding="utf-8")
            gradle_path = gradle_dir / ("gradle.bat" if os.name == "nt" else "gradle")
            gradle_path.write_text("@echo off\n" if os.name == "nt" else "#!/bin/sh\n", encoding="utf-8")

            config = AndroidConfig(
                source_dir=str(source_dir),
                output_dir=str(output_dir),
                build_mode="apk_debug",
                gradle_path=str(gradle_path),
                android_sdk_path=str(sdk_dir),
            )
            result = Builder.build_android(config)

            self.assertEqual(result["cmd"][-1], "assembleDebug")
            self.assertIn("--no-daemon", result["cmd"])
            self.assertTrue(result["artifact_dir"].endswith(os.path.join("app", "build", "outputs", "apk", "debug")))
            self.assertTrue((output_dir / "local.properties").exists())
            self.assertIn("Gradle Task: assembleDebug", result["log_text"])

    def test_build_android_rejects_output_inside_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "webapp"
            output_dir = source_dir / "android-project"
            source_dir.mkdir()
            (source_dir / "index.html").write_text("<html></html>", encoding="utf-8")

            config = AndroidConfig(source_dir=str(source_dir), output_dir=str(output_dir))

            with self.assertRaises(ValueError):
                Builder.build_android(config)

if __name__ == '__main__':
    unittest.main()

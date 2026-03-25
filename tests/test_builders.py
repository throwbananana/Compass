import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import PythonConfig, CSharpConfig, NodeConfig, JavaConfig
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

if __name__ == '__main__':
    unittest.main()

from dataclasses import dataclass
from typing import Optional

@dataclass
class PythonConfig:
    entry: str
    backend: str = 'pyinstaller'  # 'pyinstaller' or 'nuitka'
    onefile: bool = True
    noconsole: bool = False
    clean: bool = True
    interpreter: Optional[str] = None

@dataclass
class CSharpConfig:
    project_path: str
    rid: str = 'win-x64'
    self_contained: bool = True
    single_file: bool = True
    trim: bool = False

@dataclass
class NodeConfig:
    entry: str
    target: str = 'node18-win-x64'

@dataclass
class JavaConfig:
    input_path: str
    main_jar: str
    main_class: Optional[str] = None
    output_type: str = 'exe'

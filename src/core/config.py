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


@dataclass
class AndroidConfig:
    source_dir: str
    output_dir: str = ''
    start_page: str = ''
    app_name: str = ''
    package_name: str = ''
    min_sdk: int = 24
    target_sdk: int = 35
    version_code: int = 1
    version_name: str = '1.0.0'
    mobile_adapt: bool = True
    prefer_built_web_root: bool = True
    build_mode: str = 'project'  # 'project', 'apk_debug', 'apk_release', 'aab_release'
    gradle_path: str = ''
    android_sdk_path: str = ''

from __future__ import annotations

import os
import re
import shutil
import textwrap
from pathlib import Path


PRIORITY_START_FILES = ("index.html", "main.html", "home.html", "default.html")
IGNORED_NAMES = {
    ".git",
    ".gradle",
    ".idea",
    "__pycache__",
    "android",
    "android_project",
    "android-project",
    "build",
    "dist",
    "node_modules",
}
JAVA_RESERVED_WORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "false", "final", "finally", "float", "for", "goto", "if",
    "implements", "import", "instanceof", "int", "interface", "long", "native",
    "new", "null", "package", "private", "protected", "public", "return",
    "short", "static", "strictfp", "super", "switch", "synchronized", "this",
    "throw", "throws", "transient", "true", "try", "void", "volatile", "while",
}
ANDROID_BUILD_TASKS = {
    "project": None,
    "apk_debug": "assembleDebug",
    "apk_release": "assembleRelease",
    "aab_release": "bundleRelease",
}
ANDROID_OUTPUT_DIRS = {
    "project": "",
    "apk_debug": "app/build/outputs/apk/debug",
    "apk_release": "app/build/outputs/apk/release",
    "aab_release": "app/build/outputs/bundle/release",
}


def generate_android_project(config: "AndroidConfig") -> tuple[str, str]:
    source_dir = Path(config.source_dir).expanduser().resolve()
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError("Invalid source folder.")

    app_name = sanitize_app_name(config.app_name or source_dir.name)
    package_name = sanitize_package_name(config.package_name or "", app_name)
    output_dir = resolve_output_dir(source_dir, config.output_dir)
    ensure_safe_output_dir(source_dir, output_dir)

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("Output folder already exists and is not empty.")

    start_page = detect_start_page(source_dir, config.start_page)
    min_sdk = int(config.min_sdk)
    target_sdk = int(config.target_sdk)
    if min_sdk > target_sdk:
        raise ValueError("Minimum SDK cannot be greater than target SDK.")

    java_dir = output_dir / "app" / "src" / "main" / "java" / Path(*package_name.split("."))
    res_dir = output_dir / "app" / "src" / "main" / "res"
    assets_dir = output_dir / "app" / "src" / "main" / "assets" / "app"

    java_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "layout").mkdir(parents=True, exist_ok=True)
    (res_dir / "values").mkdir(parents=True, exist_ok=True)
    (res_dir / "drawable").mkdir(parents=True, exist_ok=True)
    (res_dir / "mipmap-anydpi-v26").mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    copy_source_folder(source_dir, assets_dir)

    if config.mobile_adapt:
        add_mobile_support(assets_dir)

    module_slug = sanitize_module_slug(app_name)

    write_text(output_dir / "settings.gradle", render_settings_gradle(module_slug))
    write_text(output_dir / "build.gradle", render_root_build_gradle())
    write_text(output_dir / "gradle.properties", render_gradle_properties())
    write_text(output_dir / ".gitignore", render_gitignore())
    write_text(output_dir / "README.md", render_readme(app_name, start_page, config.mobile_adapt))

    write_text(output_dir / "app" / "build.gradle", render_app_build_gradle(package_name, min_sdk, target_sdk))
    write_text(output_dir / "app" / "proguard-rules.pro", render_proguard_rules())
    write_text(output_dir / "app" / "src" / "main" / "AndroidManifest.xml", render_manifest())
    write_text(java_dir / "MainActivity.java", render_main_activity(package_name, start_page))
    write_text(res_dir / "layout" / "activity_main.xml", render_activity_layout())
    write_text(res_dir / "values" / "strings.xml", render_strings(app_name))
    write_text(res_dir / "values" / "colors.xml", render_colors())
    write_text(res_dir / "values" / "themes.xml", render_themes())
    write_text(res_dir / "drawable" / "ic_launcher_background.xml", render_launcher_background())
    write_text(res_dir / "drawable" / "ic_launcher_foreground.xml", render_launcher_foreground())
    write_text(res_dir / "mipmap-anydpi-v26" / "ic_launcher.xml", render_launcher_icon())
    write_text(res_dir / "mipmap-anydpi-v26" / "ic_launcher_round.xml", render_launcher_icon())

    log_lines = [
        "Android project generated successfully.",
        f"App Name: {app_name}",
        f"Package: {package_name}",
        f"Start Page: {start_page}",
        f"Min SDK: {min_sdk}",
        f"Target SDK: {target_sdk}",
        f"Mobile Adaptation: {'enabled' if config.mobile_adapt else 'disabled'}",
        f"Project Directory: {output_dir}",
        "",
        "Next step: open the generated folder in Android Studio and build the APK/AAB there.",
    ]
    return str(output_dir), "\n".join(log_lines)


def build_android_project(config: "AndroidConfig") -> dict:
    build_mode = config.build_mode or "project"
    if build_mode not in ANDROID_BUILD_TASKS:
        raise ValueError("Unsupported Android build mode.")

    gradle_cmd = None
    sdk_path = detect_android_sdk_path(config.android_sdk_path)

    if build_mode != "project":
        gradle_cmd = resolve_gradle_command(config.gradle_path)
        if not sdk_path:
            raise RuntimeError(
                "Android SDK not found. Select the SDK folder or set ANDROID_SDK_ROOT / ANDROID_HOME first."
            )

    project_dir, log_text = generate_android_project(config)

    if sdk_path:
        write_text(Path(project_dir) / "local.properties", render_local_properties(sdk_path))

    if build_mode == "project":
        return {
            "project_dir": project_dir,
            "log_text": log_text,
            "cmd": None,
            "cwd": project_dir,
            "artifact_dir": "",
            "build_mode": build_mode,
        }

    task = ANDROID_BUILD_TASKS[build_mode]
    artifact_dir = str((Path(project_dir) / ANDROID_OUTPUT_DIRS[build_mode]).resolve())
    build_lines = [
        "",
        f"Gradle Command: {gradle_cmd}",
        f"Android SDK: {sdk_path}",
        f"Gradle Task: {task}",
        f"Expected Output Folder: {artifact_dir}",
    ]
    return {
        "project_dir": project_dir,
        "log_text": log_text + "\n" + "\n".join(build_lines),
        "cmd": [gradle_cmd, "--no-daemon", task],
        "cwd": project_dir,
        "artifact_dir": artifact_dir,
        "build_mode": build_mode,
    }


def sanitize_app_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]+", "", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Compass Android App"


def resolve_gradle_command(custom_gradle_path: str) -> str:
    candidates = []

    if custom_gradle_path and custom_gradle_path.strip():
        candidates.append(Path(custom_gradle_path).expanduser().resolve())
    else:
        for cmd_name in ("gradlew.bat", "gradlew", "gradle.bat", "gradle"):
            path = shutil.which(cmd_name)
            if path:
                candidates.append(Path(path))

        gradle_cache_dir = Path.home() / ".gradle" / "wrapper" / "dists"
        if gradle_cache_dir.exists():
            for pattern in ("**/bin/gradle.bat", "**/bin/gradle"):
                cached = sorted(gradle_cache_dir.glob(pattern), reverse=True)
                candidates.extend(cached)

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise RuntimeError("Gradle not found. Install Gradle or select gradle.bat / gradlew.bat first.")


def detect_android_sdk_path(custom_sdk_path: str) -> str:
    candidates = []
    if custom_sdk_path and custom_sdk_path.strip():
        candidates.append(Path(custom_sdk_path).expanduser().resolve())

    for env_name in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        env_value = os.environ.get(env_name, "").strip()
        if env_value:
            candidates.append(Path(env_value).expanduser().resolve())

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        candidates.append(Path(local_app_data) / "Android" / "Sdk")

    home = Path.home()
    candidates.append(home / "AppData" / "Local" / "Android" / "Sdk")
    candidates.append(home / "Android" / "Sdk")

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return str(candidate.resolve())

    return ""


def sanitize_module_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "compass-android-app"


def sanitize_package_name(package_name: str, app_name: str) -> str:
    base = package_name.strip().lower()
    if not base:
        app_part = re.sub(r"[^a-z0-9]+", "", app_name.lower()) or "app"
        return f"com.compass.{app_part}"

    sanitized_parts = []
    for raw_part in base.split("."):
        part = re.sub(r"[^a-z0-9_]+", "_", raw_part).strip("_")
        if not part:
            continue
        if part[0].isdigit():
            part = f"app_{part}"
        if part in JAVA_RESERVED_WORDS:
            part = f"{part}_app"
        sanitized_parts.append(part)

    if len(sanitized_parts) < 2:
        app_part = re.sub(r"[^a-z0-9]+", "", app_name.lower()) or "app"
        sanitized_parts = ["com", "compass", app_part]

    return ".".join(sanitized_parts)


def resolve_output_dir(source_dir: Path, output_dir: str) -> Path:
    if output_dir and output_dir.strip():
        return Path(output_dir).expanduser().resolve()
    return (source_dir.parent / f"{source_dir.name}-android-project").resolve()


def ensure_safe_output_dir(source_dir: Path, output_dir: Path) -> None:
    if output_dir == source_dir:
        raise ValueError("Output folder must be different from the source folder.")

    try:
        output_dir.relative_to(source_dir)
    except ValueError:
        return

    raise ValueError("Output folder cannot be inside the source folder.")


def detect_start_page(source_dir: Path, requested_start_page: str) -> str:
    if requested_start_page and requested_start_page.strip():
        start_page = resolve_source_relative_path(source_dir, requested_start_page)
        if start_page.suffix.lower() not in {".html", ".htm"}:
            raise ValueError("Start page must be an HTML file.")
        if not start_page.exists():
            raise ValueError("Selected start page does not exist.")
        return start_page.relative_to(source_dir).as_posix()

    html_files = sorted(
        (
            path for path in source_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".html", ".htm"}
        ),
        key=html_sort_key,
    )
    if not html_files:
        raise ValueError("No HTML entry file found in the selected folder.")

    return html_files[0].relative_to(source_dir).as_posix()


def resolve_source_relative_path(source_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    resolved = path.resolve() if path.is_absolute() else (source_dir / path).resolve()

    try:
        resolved.relative_to(source_dir)
    except ValueError as exc:
        raise ValueError("Start page must be inside the selected source folder.") from exc

    return resolved


def html_sort_key(path: Path) -> tuple[int, int, str]:
    name = path.name.lower()
    priority = PRIORITY_START_FILES.index(name) if name in PRIORITY_START_FILES else len(PRIORITY_START_FILES)
    return priority, len(path.parts), path.as_posix().lower()


def copy_source_folder(source_dir: Path, assets_dir: Path) -> None:
    ignore = shutil.ignore_patterns(*IGNORED_NAMES)
    shutil.copytree(source_dir, assets_dir, dirs_exist_ok=True, ignore=ignore)


def add_mobile_support(assets_dir: Path) -> None:
    write_text(assets_dir / "compass-mobile-adapter.css", render_mobile_css())
    write_text(assets_dir / "compass-mobile-adapter.js", render_mobile_js())

    html_files = [
        path for path in assets_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".htm"}
    ]
    for html_path in html_files:
        raw_html = html_path.read_text(encoding="utf-8", errors="ignore")
        rel_prefix = os.path.relpath(assets_dir, html_path.parent).replace("\\", "/")
        asset_prefix = "" if rel_prefix == "." else f"{rel_prefix}/"
        html_path.write_text(inject_mobile_tags(raw_html, asset_prefix), encoding="utf-8")


def inject_mobile_tags(raw_html: str, asset_prefix: str) -> str:
    updated = raw_html
    lowered = updated.lower()

    viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">'
    css_tag = f'<link rel="stylesheet" href="{asset_prefix}compass-mobile-adapter.css">'
    js_tag = f'<script src="{asset_prefix}compass-mobile-adapter.js"></script>'

    if "name=\"viewport\"" not in lowered:
        updated = inject_into_head(updated, viewport_tag)
        lowered = updated.lower()

    if "compass-mobile-adapter.css" not in lowered:
        updated = inject_into_head(updated, css_tag)
        lowered = updated.lower()

    if "compass-mobile-adapter.js" not in lowered:
        updated = inject_before_body_close(updated, js_tag)

    return updated


def inject_into_head(raw_html: str, snippet: str) -> str:
    match = re.search(r"</head\s*>", raw_html, flags=re.IGNORECASE)
    if match:
        return f"{raw_html[:match.start()]}    {snippet}\n{raw_html[match.start():]}"

    html_open = re.search(r"<html[^>]*>", raw_html, flags=re.IGNORECASE)
    if html_open:
        head_block = f"\n<head>\n    {snippet}\n</head>\n"
        return f"{raw_html[:html_open.end()]}{head_block}{raw_html[html_open.end():]}"

    body_open = re.search(r"<body[^>]*>", raw_html, flags=re.IGNORECASE)
    if body_open:
        head_block = f"<head>\n    {snippet}\n</head>\n"
        return f"{raw_html[:body_open.start()]}{head_block}{raw_html[body_open.start():]}"

    return f"<head>\n    {snippet}\n</head>\n{raw_html}"


def inject_before_body_close(raw_html: str, snippet: str) -> str:
    match = re.search(r"</body\s*>", raw_html, flags=re.IGNORECASE)
    if match:
        return f"{raw_html[:match.start()]}    {snippet}\n{raw_html[match.start():]}"

    html_close = re.search(r"</html\s*>", raw_html, flags=re.IGNORECASE)
    if html_close:
        return f"{raw_html[:html_close.start()]}    {snippet}\n{raw_html[html_close.start():]}"

    return f"{raw_html}\n{snippet}\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def render_local_properties(sdk_path: str) -> str:
    escaped_path = str(Path(sdk_path).resolve()).replace("\\", "\\\\").replace(":", "\\:")
    return f"sdk.dir={escaped_path}"


def render_settings_gradle(module_slug: str) -> str:
    return textwrap.dedent(
        f"""
        pluginManagement {{
            repositories {{
                google()
                mavenCentral()
                gradlePluginPortal()
            }}
        }}

        dependencyResolutionManagement {{
            repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
            repositories {{
                google()
                mavenCentral()
            }}
        }}

        rootProject.name = "{module_slug}"
        include(":app")
        """
    )


def render_root_build_gradle() -> str:
    return textwrap.dedent(
        """
        plugins {
            id 'com.android.application' version '8.5.2' apply false
        }
        """
    )


def render_gradle_properties() -> str:
    return textwrap.dedent(
        """
        org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
        android.useAndroidX=true
        android.nonTransitiveRClass=true
        """
    )


def render_gitignore() -> str:
    return textwrap.dedent(
        """
        .gradle/
        .idea/
        *.iml
        local.properties
        build/
        app/build/
        captures/
        """
    )


def render_readme(app_name: str, start_page: str, mobile_adapt: bool) -> str:
    adaptation_line = "- Injects `compass-mobile-adapter.css` and `compass-mobile-adapter.js` into HTML files" if mobile_adapt else "- Keeps copied assets untouched; mobile WebView behavior still stays enabled in native code"
    return textwrap.dedent(
        f"""
        # {app_name}

        This Android Studio project was generated by Compass from a local web folder.

        ## Included behavior
        - Loads the packaged site from `app/src/main/assets/app/{start_page}`
        - Enables mobile-friendly WebView settings, pull-to-refresh, back navigation, and responsive viewport helpers
        {adaptation_line}

        ## Build
        1. Open this folder in Android Studio.
        2. Let Gradle sync.
        3. Use `Build > Build Bundle(s) / APK(s)` to produce an installable package.

        ## Notes
        - Source web assets are copied to `app/src/main/assets/app`.
        - If your site depends on remote HTTP resources, cleartext traffic is enabled by default.
        """
    )


def render_app_build_gradle(package_name: str, min_sdk: int, target_sdk: int) -> str:
    return textwrap.dedent(
        f"""
        plugins {{
            id 'com.android.application'
        }}

        android {{
            namespace '{package_name}'
            compileSdk {target_sdk}

            defaultConfig {{
                applicationId '{package_name}'
                minSdk {min_sdk}
                targetSdk {target_sdk}
                versionCode 1
                versionName '1.0'
            }}

            buildTypes {{
                release {{
                    minifyEnabled false
                    proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
                }}
            }}

            compileOptions {{
                sourceCompatibility JavaVersion.VERSION_17
                targetCompatibility JavaVersion.VERSION_17
            }}
        }}

        dependencies {{
            implementation 'androidx.appcompat:appcompat:1.7.0'
            implementation 'androidx.webkit:webkit:1.11.0'
            implementation 'androidx.swiperefreshlayout:swiperefreshlayout:1.1.0'
        }}
        """
    )


def render_proguard_rules() -> str:
    return "# Generated by Compass.\n"


def render_manifest() -> str:
    return textwrap.dedent(
        """
        <?xml version="1.0" encoding="utf-8"?>
        <manifest xmlns:android="http://schemas.android.com/apk/res/android">

            <uses-permission android:name="android.permission.INTERNET" />

            <application
                android:allowBackup="true"
                android:hardwareAccelerated="true"
                android:icon="@mipmap/ic_launcher"
                android:label="@string/app_name"
                android:resizeableActivity="true"
                android:roundIcon="@mipmap/ic_launcher_round"
                android:supportsRtl="true"
                android:theme="@style/Theme.CompassAndroid"
                android:usesCleartextTraffic="true">
                <activity
                    android:name=".MainActivity"
                    android:configChanges="keyboard|keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize|uiMode"
                    android:exported="true"
                    android:launchMode="singleTask"
                    android:windowSoftInputMode="adjustResize">
                    <intent-filter>
                        <action android:name="android.intent.action.MAIN" />

                        <category android:name="android.intent.category.LAUNCHER" />
                    </intent-filter>
                </activity>
            </application>

        </manifest>
        """
    )


def render_main_activity(package_name: str, start_page: str) -> str:
    safe_start_page = start_page.replace("\\", "/").lstrip("/")
    return textwrap.dedent(
        f"""
        package {package_name};

        import android.content.ActivityNotFoundException;
        import android.content.Intent;
        import android.graphics.Color;
        import android.net.Uri;
        import android.os.Bundle;
        import android.view.View;
        import android.webkit.MimeTypeMap;
        import android.webkit.WebChromeClient;
        import android.webkit.WebResourceRequest;
        import android.webkit.WebResourceResponse;
        import android.webkit.WebSettings;
        import android.webkit.WebView;

        import androidx.activity.OnBackPressedCallback;
        import androidx.annotation.NonNull;
        import androidx.annotation.Nullable;
        import androidx.appcompat.app.AppCompatActivity;
        import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;
        import androidx.webkit.WebViewAssetLoader;
        import androidx.webkit.WebViewClientCompat;

        import java.io.IOException;
        import java.io.InputStream;
        import java.net.URLConnection;
        import java.util.Locale;

        public class MainActivity extends AppCompatActivity {{
            private static final String LOCAL_ROOT = "https://appassets.androidplatform.net/app/";
            private static final String START_PAGE = "{safe_start_page}";

            private SwipeRefreshLayout swipeRefreshLayout;
            private WebView webView;
            private WebViewAssetLoader assetLoader;

            @Override
            protected void onCreate(Bundle savedInstanceState) {{
                super.onCreate(savedInstanceState);
                setContentView(R.layout.activity_main);

                swipeRefreshLayout = findViewById(R.id.swipe_refresh);
                webView = findViewById(R.id.web_view);
                assetLoader = new WebViewAssetLoader.Builder()
                    .setDomain("appassets.androidplatform.net")
                    .addPathHandler("/app/", new LocalAppPathHandler())
                    .build();

                configureWebView();
                configureRefresh();
                configureBackHandling();

                if (savedInstanceState != null) {{
                    webView.restoreState(savedInstanceState);
                }} else {{
                    webView.loadUrl(LOCAL_ROOT + START_PAGE);
                }}
            }}

            @Override
            protected void onSaveInstanceState(@NonNull Bundle outState) {{
                super.onSaveInstanceState(outState);
                webView.saveState(outState);
            }}

            @Override
            protected void onDestroy() {{
                if (webView != null) {{
                    webView.destroy();
                }}
                super.onDestroy();
            }}

            private void configureWebView() {{
                WebSettings settings = webView.getSettings();
                settings.setJavaScriptEnabled(true);
                settings.setDomStorageEnabled(true);
                settings.setDatabaseEnabled(true);
                settings.setAllowContentAccess(true);
                settings.setAllowFileAccess(true);
                settings.setMediaPlaybackRequiresUserGesture(false);
                settings.setLoadWithOverviewMode(true);
                settings.setUseWideViewPort(true);
                settings.setSupportZoom(true);
                settings.setBuiltInZoomControls(true);
                settings.setDisplayZoomControls(false);
                settings.setTextZoom(100);

                webView.setBackgroundColor(Color.TRANSPARENT);
                webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
                webView.setWebChromeClient(new WebChromeClient());
                webView.setWebViewClient(new LocalWebViewClient());
            }}

            private void configureRefresh() {{
                swipeRefreshLayout.setOnRefreshListener(() -> webView.reload());
                webView.setOnScrollChangeListener((view, scrollX, scrollY, oldScrollX, oldScrollY) ->
                    swipeRefreshLayout.setEnabled(scrollY == 0)
                );
            }}

            private void configureBackHandling() {{
                getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {{
                    @Override
                    public void handleOnBackPressed() {{
                        if (webView.canGoBack()) {{
                            webView.goBack();
                        }} else {{
                            finish();
                        }}
                    }}
                }});
            }}

            private final class LocalWebViewClient extends WebViewClientCompat {{
                @Nullable
                @Override
                public WebResourceResponse shouldInterceptRequest(@NonNull WebView view, @NonNull WebResourceRequest request) {{
                    return assetLoader.shouldInterceptRequest(request.getUrl());
                }}

                @Override
                public boolean shouldOverrideUrlLoading(@NonNull WebView view, @NonNull WebResourceRequest request) {{
                    Uri uri = request.getUrl();
                    if ("appassets.androidplatform.net".equalsIgnoreCase(uri.getHost())) {{
                        return false;
                    }}

                    String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase(Locale.ROOT);
                    if ("http".equals(scheme) || "https".equals(scheme) || "mailto".equals(scheme) || "tel".equals(scheme) || "sms".equals(scheme)) {{
                        try {{
                            startActivity(new Intent(Intent.ACTION_VIEW, uri));
                            return true;
                        }} catch (ActivityNotFoundException ignored) {{
                            return false;
                        }}
                    }}

                    return false;
                }}

                @Override
                public void onPageFinished(@NonNull WebView view, @NonNull String url) {{
                    super.onPageFinished(view, url);
                    swipeRefreshLayout.setRefreshing(false);
                }}
            }}

            private final class LocalAppPathHandler implements WebViewAssetLoader.PathHandler {{
                @Nullable
                @Override
                public WebResourceResponse handle(@NonNull String path) {{
                    String assetPath = normalizePath(path);
                    try {{
                        return openAsset(assetPath);
                    }} catch (IOException ignored) {{
                        if (shouldServeStartPage(assetPath)) {{
                            try {{
                                return openAsset(START_PAGE);
                            }} catch (IOException ignoredAgain) {{
                                return null;
                            }}
                        }}
                        return null;
                    }}
                }}
            }}

            @NonNull
            private String normalizePath(@Nullable String rawPath) {{
                if (rawPath == null || rawPath.trim().isEmpty()) {{
                    return START_PAGE;
                }}

                String cleaned = rawPath.startsWith("/") ? rawPath.substring(1) : rawPath;
                return cleaned.isEmpty() ? START_PAGE : cleaned;
            }}

            private boolean shouldServeStartPage(@NonNull String assetPath) {{
                String lastSegment = assetPath.substring(assetPath.lastIndexOf('/') + 1);
                return !lastSegment.contains(".");
            }}

            @NonNull
            private WebResourceResponse openAsset(@NonNull String assetPath) throws IOException {{
                InputStream stream = getAssets().open("app/" + assetPath);
                String mimeType = guessMimeType(assetPath);
                String encoding = mimeType.startsWith("text/") || mimeType.contains("javascript") || mimeType.contains("json")
                    ? "UTF-8"
                    : null;
                return new WebResourceResponse(mimeType, encoding, stream);
            }}

            @NonNull
            private String guessMimeType(@NonNull String assetPath) {{
                String extension = MimeTypeMap.getFileExtensionFromUrl(assetPath);
                String mimeType = extension == null ? null : MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension.toLowerCase(Locale.ROOT));
                if (mimeType == null) {{
                    mimeType = URLConnection.guessContentTypeFromName(assetPath);
                }}
                return mimeType == null ? "application/octet-stream" : mimeType;
            }}
        }}
        """
    )


def render_activity_layout() -> str:
    return textwrap.dedent(
        """
        <?xml version="1.0" encoding="utf-8"?>
        <androidx.swiperefreshlayout.widget.SwipeRefreshLayout
            xmlns:android="http://schemas.android.com/apk/res/android"
            android:id="@+id/swipe_refresh"
            android:layout_width="match_parent"
            android:layout_height="match_parent">

            <WebView
                android:id="@+id/web_view"
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:overScrollMode="never"
                android:scrollbarStyle="outsideOverlay" />

        </androidx.swiperefreshlayout.widget.SwipeRefreshLayout>
        """
    )


def render_strings(app_name: str) -> str:
    escaped_app_name = escape_xml(app_name)
    return textwrap.dedent(
        f"""
        <?xml version="1.0" encoding="utf-8"?>
        <resources>
            <string name="app_name">{escaped_app_name}</string>
        </resources>
        """
    )


def render_colors() -> str:
    return textwrap.dedent(
        """
        <?xml version="1.0" encoding="utf-8"?>
        <resources>
            <color name="compass_primary">#0B4F6C</color>
            <color name="compass_primary_dark">#083B52</color>
            <color name="compass_accent">#22B8CF</color>
            <color name="compass_background">#08131A</color>
        </resources>
        """
    )


def render_themes() -> str:
    return textwrap.dedent(
        """
        <?xml version="1.0" encoding="utf-8"?>
        <resources>
            <style name="Theme.CompassAndroid" parent="Theme.AppCompat.DayNight.NoActionBar">
                <item name="colorPrimary">@color/compass_primary</item>
                <item name="colorPrimaryDark">@color/compass_primary_dark</item>
                <item name="colorAccent">@color/compass_accent</item>
                <item name="android:statusBarColor">@android:color/transparent</item>
                <item name="android:navigationBarColor">@color/compass_background</item>
                <item name="android:windowBackground">@color/compass_background</item>
            </style>
        </resources>
        """
    )


def render_launcher_background() -> str:
    return textwrap.dedent(
        """
        <?xml version="1.0" encoding="utf-8"?>
        <shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
            <solid android:color="#08131A" />
        </shape>
        """
    )


def render_launcher_foreground() -> str:
    return textwrap.dedent(
        """
        <?xml version="1.0" encoding="utf-8"?>
        <vector xmlns:android="http://schemas.android.com/apk/res/android"
            android:width="108dp"
            android:height="108dp"
            android:viewportWidth="108"
            android:viewportHeight="108">
            <path
                android:fillColor="#22B8CF"
                android:pathData="M54,12 L79,54 L54,96 L29,54 Z" />
            <path
                android:fillColor="#FFFFFF"
                android:pathData="M54,22 L66,54 L54,86 L42,54 Z" />
            <path
                android:fillColor="#0B4F6C"
                android:pathData="M54,30 L60,54 L54,78 L48,54 Z" />
        </vector>
        """
    )


def render_launcher_icon() -> str:
    return textwrap.dedent(
        """
        <?xml version="1.0" encoding="utf-8"?>
        <adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
            <background android:drawable="@drawable/ic_launcher_background" />
            <foreground android:drawable="@drawable/ic_launcher_foreground" />
            <monochrome android:drawable="@drawable/ic_launcher_foreground" />
        </adaptive-icon>
        """
    )


def render_mobile_css() -> str:
    return textwrap.dedent(
        """
        :root {
            --app-vh: 1vh;
        }

        html {
            -webkit-text-size-adjust: 100%;
            text-size-adjust: 100%;
            touch-action: manipulation;
        }

        body {
            min-height: calc(var(--app-vh) * 100);
            margin: 0;
            padding-top: max(env(safe-area-inset-top), 0px);
            padding-right: max(env(safe-area-inset-right), 0px);
            padding-bottom: max(env(safe-area-inset-bottom), 0px);
            padding-left: max(env(safe-area-inset-left), 0px);
            overscroll-behavior-y: contain;
            overflow-x: hidden;
        }

        *,
        *::before,
        *::after {
            box-sizing: border-box;
        }

        img,
        video,
        canvas,
        svg,
        iframe {
            max-width: 100%;
            height: auto;
        }

        input,
        button,
        select,
        textarea,
        a {
            touch-action: manipulation;
        }
        """
    )


def render_mobile_js() -> str:
    return textwrap.dedent(
        """
        (function () {
            var root = document.documentElement;

            function updateViewportHeight() {
                root.style.setProperty("--app-vh", (window.innerHeight * 0.01) + "px");
            }

            function updateOrientationFlag() {
                root.dataset.orientation = window.innerWidth >= window.innerHeight ? "landscape" : "portrait";
            }

            function scrollFocusedFieldIntoView(event) {
                var target = event.target;
                if (!target || !target.tagName) {
                    return;
                }

                var tag = target.tagName.toUpperCase();
                if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
                    window.setTimeout(function () {
                        target.scrollIntoView({ block: "center", behavior: "smooth" });
                    }, 180);
                }
            }

            updateViewportHeight();
            updateOrientationFlag();

            window.addEventListener("resize", function () {
                updateViewportHeight();
                updateOrientationFlag();
            }, { passive: true });

            window.addEventListener("orientationchange", function () {
                window.setTimeout(function () {
                    updateViewportHeight();
                    updateOrientationFlag();
                }, 180);
            }, { passive: true });

            document.addEventListener("focusin", scrollFocusedFieldIntoView, { passive: true });
        }());
        """
    )


def escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

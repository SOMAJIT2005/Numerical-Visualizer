"""
c_bridge.py — C Engine Build & Subprocess Bridge for Numerical Methods Lab.
Ensures all mathematical calculations execute in compiled C binaries:
  - build/engine.exe        (src/engine_main.c, src/roots.c, src/tinyexpr.c)
  - build/matrix_engine.exe (src/matrix_main.c, src/linalg.c)
  - build/numlab_engine.exe (src/numlab_main.c, src/numlab.c, src/tinyexpr.c)
"""
import os
import glob
import shutil
import subprocess
from config import resource_path

_COMPILE_CHECKED = False


def _find_c_compiler():
    """Locate gcc or clang on PATH or standard Windows toolchain directories."""
    for env_key in ('CC', 'GCC'):
        cc = os.environ.get(env_key)
        if cc and (shutil.which(cc) or os.path.isfile(cc)):
            return cc

    for name in ('gcc', 'clang', 'x86_64-w64-mingw32-gcc'):
        found = shutil.which(name)
        if found:
            return found

    candidates = [
        r"C:\msys64\mingw64\bin\gcc.exe",
        r"C:\msys64\ucrt64\bin\gcc.exe",
        r"C:\msys64\clang64\bin\gcc.exe",
        r"C:\MinGW\bin\gcc.exe",
        r"C:\TDM-GCC-64\bin\gcc.exe",
        r"C:\ProgramData\mingw64\mingw64\bin\gcc.exe",
        r"C:\Strawberry\c\bin\gcc.exe",
        r"C:\w64devkit\bin\gcc.exe",
    ]
    for pattern in (
        r"C:\Program Files\mingw-w64\*\mingw64\bin\gcc.exe",
        r"C:\Program Files (x86)\mingw-w64\*\mingw32\bin\gcc.exe",
        r"C:\Users\*\scoop\apps\gcc\current\bin\gcc.exe",
        r"C:\Users\*\scoop\apps\mingw\current\bin\gcc.exe",
        r"C:\Users\*\AppData\Local\Programs\**\gcc.exe",
    ):
        candidates.extend(glob.glob(pattern))

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _needs_rebuild(target_path, source_paths):
    if not os.path.isfile(target_path):
        return True
    target_mtime = os.path.getmtime(target_path)
    for src in source_paths:
        if os.path.isfile(src) and os.path.getmtime(src) > target_mtime:
            return True
    return False


def ensure_c_engines_built(force=False):
    """Auto-compile C engines if source files in src/ or include/ are newer than build/*.exe."""
    global _COMPILE_CHECKED
    if _COMPILE_CHECKED and not force:
        return True
    _COMPILE_CHECKED = True

    base_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(base_dir, 'build')
    os.makedirs(build_dir, exist_ok=True)

    targets = [
        (
            os.path.join(build_dir, 'engine.exe'),
            [
                os.path.join(base_dir, 'src', 'engine_main.c'),
                os.path.join(base_dir, 'src', 'roots.c'),
                os.path.join(base_dir, 'src', 'tinyexpr.c'),
            ],
            [
                os.path.join(base_dir, 'include', 'roots.h'),
                os.path.join(base_dir, 'include', 'tinyexpr.h'),
            ],
        ),
        (
            os.path.join(build_dir, 'matrix_engine.exe'),
            [
                os.path.join(base_dir, 'src', 'matrix_main.c'),
                os.path.join(base_dir, 'src', 'linalg.c'),
            ],
            [
                os.path.join(base_dir, 'include', 'linalg.h'),
            ],
        ),
        (
            os.path.join(build_dir, 'numlab_engine.exe'),
            [
                os.path.join(base_dir, 'src', 'numlab_main.c'),
                os.path.join(base_dir, 'src', 'numlab.c'),
                os.path.join(base_dir, 'src', 'tinyexpr.c'),
            ],
            [
                os.path.join(base_dir, 'include', 'numlab.h'),
                os.path.join(base_dir, 'include', 'tinyexpr.h'),
            ],
        ),
    ]

    cc = None
    for exe_path, c_files, h_files in targets:
        if force or _needs_rebuild(exe_path, c_files + h_files):
            if cc is None:
                cc = _find_c_compiler()
            if not cc:
                break
            # Try static linking first so bundled .exe has zero external MinGW DLL dependencies
            cmd_static = [cc, *c_files, f"-I{os.path.join(base_dir, 'include')}", "-O3", "-static", "-o", exe_path, "-lm"]
            cmd_fallback = [cc, *c_files, f"-I{os.path.join(base_dir, 'include')}", "-O3", "-o", exe_path, "-lm"]
            try:
                res = subprocess.run(
                    cmd_static,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
                if res.returncode != 0:
                    subprocess.run(
                        cmd_fallback,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                    )
            except Exception:
                pass
    return all(os.path.isfile(t[0]) for t in targets)


def _run_c_binary(rel_exe_path, args, timeout=15):
    ensure_c_engines_built()
    exe_path = resource_path(rel_exe_path)
    if not os.path.isfile(exe_path):
        raise FileNotFoundError(
            f"Compiled C engine '{rel_exe_path}' not found.\n"
            f"Please run 'make' (or gcc) in the project root to compile the C math engines."
        )
    str_args = [exe_path] + [str(a) for a in args]
    res = subprocess.run(
        str_args,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    output = (res.stdout or "").strip()
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("ERROR,"):
            raise ValueError(line.split(",", 1)[1])
    if res.returncode != 0 and not lines:
        err_msg = (res.stderr or "C engine returned non-zero status").strip()
        raise RuntimeError(err_msg)
    return lines


def run_root_engine(args):
    """Execute build/engine.exe with arguments and return stdout lines."""
    return _run_c_binary("build/engine.exe", args)


def run_matrix_engine(args):
    """Execute build/matrix_engine.exe with arguments and return stdout lines."""
    return _run_c_binary("build/matrix_engine.exe", args)


def run_numlab_engine(args):
    """Execute build/numlab_engine.exe with arguments and return stdout lines."""
    return _run_c_binary("build/numlab_engine.exe", args)

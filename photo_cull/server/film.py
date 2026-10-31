"""和「胶片冲印」（photo-cull-film）的连接。

胶片冲印是单独的程序、单独的仓库（GPLv3，因为它用了 GPLv3 的 spektrafilm），运行在自己的 Python 3.13 环境里。
照片工具（MIT）不导入它的任何代码，只做三件事：
  · 看它装没装：~/.photo-cull/apps/film-install.json（胶片冲印每次启动时写，记着它的 Python 和文件夹）；
  · 看它在不在运行：~/.photo-cull/apps/film.json ＋ /ping；
  · 需要时用它自己的 Python 把它作为独立进程启动起来，然后把它的网页放进一体窗口的第三个页签。
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote

from ..paths import CONFIG_DIR

REGISTRY = CONFIG_DIR / "apps" / "film.json"
INSTALL = CONFIG_DIR / "apps" / "film-install.json"
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def install_info() -> dict | None:
    try:
        d = json.loads(INSTALL.read_text(encoding="utf-8"))
        if Path(d["python"]).is_file() and Path(d["root"]).is_dir():
            return d
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def installed() -> bool:
    return install_info() is not None or running() is not None


def running() -> str | None:
    """在运行就返回它的地址（带令牌），否则 None。"""
    try:
        d = json.loads(REGISTRY.read_text(encoding="utf-8"))
        with _OPENER.open(f"http://127.0.0.1:{int(d['port'])}/ping", timeout=0.6) as r:
            if json.loads(r.read().decode("utf-8")).get("app") == "film":
                return f"http://127.0.0.1:{int(d['port'])}/?t={quote(d['token'])}"
    except Exception:
        pass
    return None


def start(wait: float = 30.0) -> str | None:
    """没在运行就用它自己的 Python 启动（独立进程），等它起来。返回地址；没装或起不来返回 None。"""
    url = running()
    if url:
        return url
    d = install_info()
    if not d:
        return None
    # 打包成 Mac 应用后，本进程的环境变量里有 PyInstaller 的设置，不能带给另一个 Python
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "_PYI", "_MEI", "DYLD_"))}
    env["PHOTO_CULL_NO_BROWSER"] = "1"
    try:
        subprocess.Popen([d["python"], "-m", "photo_cull_film", "--no-browser"], cwd=d["root"], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                         start_new_session=True)
    except OSError:
        return None
    end = time.time() + wait
    while time.time() < end:
        url = running()
        if url:
            return url
        time.sleep(0.3)
    return None

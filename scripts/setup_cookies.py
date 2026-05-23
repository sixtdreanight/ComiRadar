#!/usr/bin/env python3
"""从本地浏览器自动提取 B站/大麦 Cookie，写入 .env 或上传 GitHub Secrets。"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import browser_cookie3
except ImportError:
    print("需要 browser-cookie3 库来读取浏览器 Cookie。")
    answer = input("是否安装？[y/N] ").strip().lower()
    if answer not in ("y", "yes"):
        print("已取消。请手动安装: pip install browser-cookie3")
        sys.exit(1)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "browser-cookie3>=0.20,<1"])
    import browser_cookie3

DOMAINS = {
    "bilibili": {
        "domain": "bilibili.com",
        "keys": {"buvid3": "BILI_BUVID3", "SESSDATA": "BILI_SESSDATA", "bili_jct": "BILI_BILI_JCT"},
    },
    "damai": {
        "domain": "damai.cn",
        "keys": {"_m_h5_tk": "DAMAI_M_H5_TK", "cookie2": "DAMAI_COOKIE2"},
    },
}

ENV_FILE = Path(__file__).parent.parent / ".env"


def extract_cookies():
    results = {}
    browsers = []
    for name in ["chrome", "chromium", "edge", "firefox"]:
        try:
            cj = getattr(browser_cookie3, name)(domain_name=None)
            browsers.append(name)
            for label, info in DOMAINS.items():
                if label in results:
                    continue
                found = {}
                for cookie_name, _ in info["keys"].items():
                    for c in cj:
                        if info["domain"] in c.domain and c.name == cookie_name and c.value:
                            found[cookie_name] = c.value
                            break
                if len(found) >= 2:
                    results[label] = found
                    print(f"  [{name}] {label}: {len(found)} cookies")
        except Exception:
            continue
    if not browsers:
        print("未检测到浏览器。请确保 Chrome/Edge 已安装。")
        return None
    print(f"\n检测到浏览器: {', '.join(browsers)}")
    return results


def write_env(cookies: dict):
    lines = []
    for label, info in DOMAINS.items():
        found = cookies.get(label, {})
        for cookie_name, env_key in info["keys"].items():
            val = found.get(cookie_name, "")
            if val:
                lines.append(f"{env_key}={val}")
                print(f"  {env_key}=***{val[-4:]}")
            else:
                print(f"  {env_key}= (未找到)")
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except (OSError, NotImplementedError):
        pass  # Windows 不支持 os.chmod 限制权限
    print(f"\n已写入 {ENV_FILE}")


def upload_github(cookies: dict):
    """通过 gh CLI 上传到 GitHub Secrets。"""
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("gh CLI 未安装，跳过上传。请手动在 GitHub 网页添加。")
        return
    repo = subprocess.check_output(
        ["git", "config", "--get", "remote.origin.url"], text=True, cwd=ENV_FILE.parent.parent
    ).strip()
    repo = repo.replace("git@github.com:", "").replace("https://github.com/", "").replace(".git", "")
    print(f"\n上传到 {repo} ...")
    for label, info in DOMAINS.items():
        found = cookies.get(label, {})
        for cookie_name, env_key in info["keys"].items():
            val = found.get(cookie_name, "")
            if val:
                subprocess.run(
                    ["gh", "secret", "set", env_key, "--repo", repo],
                    input=val, text=True, check=False,
                )
                print(f"  {env_key} ✓")
            else:
                print(f"  {env_key} 跳过（未找到）")
    print("上传完成。")


def manual_input():
    """浏览器 DevTools 手动提取方式"""
    results = {}
    for label, info in DOMAINS.items():
        print(f"\n--- {label} ---")
        print(f"请在浏览器打开 {info['domain']}，登录后 F12 → Console，粘贴以下代码：")
        print()
        names = list(info["keys"].keys())
        js = "copy(JSON.stringify({" + ",".join(f'"{n}":document.cookie.match(/(?:^|;\\s*){n}=([^;]*)/)?.[1]||""' for n in names) + "}))"
        print(f"  {js}")
        print()
        inp = input("粘贴运行后复制的内容 (回车跳过): ").strip()
        if inp:
            try:
                data = json.loads(inp)
                found = {k: v for k, v in data.items() if v}
                results[label] = found
                print(f"  ✓ {len(found)} 个 Cookie")
            except json.JSONDecodeError:
                print("  格式错误，跳过")
    return results if results else None


def main():
    print("ComiRadar Cookie 提取工具\n")
    print("[1] 自动从浏览器读取")
    print("[2] 手动粘贴 (推荐，更可靠)")
    choice = input("选择 [1/2] (默认 2): ").strip() or "2"
    if choice == "1":
        cookies = extract_cookies()
    else:
        cookies = manual_input()
    if not cookies:
        print("\n未获取到任何 Cookie。")
        return 1
    write_env(cookies)
    print()
    answer = input("上传到 GitHub Secrets? [y/N] ").strip().lower()
    if answer in ("y", "yes"):
        upload_github(cookies)
    print("\n完成。运行 python scraper/main.py run 即可测试。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

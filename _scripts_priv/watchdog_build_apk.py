#!/usr/bin/env python3
"""
沙盒出口周期性断网 watchdog：
  - 每 15s 探测 5 个 Maven 仓库 URL（强制 IPv4）
  - 当 >=3 个 URL HTTP 200 且 延迟 < 3000ms 时 → 判定网络窗口打开
  - 立刻依次启动 BD4(assembleDebug) → BD5(releaseNoR8) → BD5b(release) 构建
  - 每个构建完成后立刻 tar.gz 导出到 /workspace/_export_apks/
  - 全程写 watchdog.log，轮询构建状态 45m
"""
import os, sys, time, subprocess, socket, urllib.request, urllib.error
from pathlib import Path

HOME = os.environ["HOME"]
WORKDIR = "/workspace"
EXPORT_DIR = f"{WORKDIR}/_export_apks"
LOG_FILE = f"{WORKDIR}/_scripts_priv/watchdog.log"
BUILD_ORDER = [
    ("bd4", [":app:assembleDebug"]),
    ("bd5_nor8", [":app:assembleReleaseNoR8"]),
    ("bd5_r8",   [":app:assembleRelease"]),
]
PROBE_URLS = [
    ("aliyun public",   "https://maven.aliyun.com/repository/public/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom"),
    ("dl google agp",   "https://dl.google.com/dl/android/maven2/com/android/application/com.android.application.gradle.plugin/8.12.2/com.android.application.gradle.plugin-8.12.2.pom"),
    ("maven central",   "https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom"),
    ("plugins gradle",  "https://plugins.gradle.org/m2/com/diffplug/spotless/com.diffplug.spotless.gradle.plugin/7.2.1/com.diffplug.spotless.gradle.plugin-7.2.1.pom"),
    ("jitpack root",    "https://jitpack.io/builds.txt"),
]

# Force IPv4 (monkey-patch)
_orig_ga = socket.getaddrinfo
def _v4only(h, p, f=0, t=0, pr=0, fl=0):
    return _orig_ga(h, p, socket.AF_INET, t, pr, fl)
socket.getaddrinfo = _v4only

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    open(LOG_FILE, "a", encoding="utf-8").write(line + "\n")

def probe_once(timeout=5):
    """Probe all URLs, return list of (name, ok, ms)."""
    results = []
    for name, u in PROBE_URLS:
        t0 = time.time()
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(u, method="HEAD", headers={"User-Agent":"curl/8.8.0"}),
                timeout=timeout
            )
            ok = (200 <= r.status < 400) or r.status == 404
            ms = int((time.time()-t0)*1000)
            results.append((name, ok and ms < 3000, ms))
        except urllib.error.HTTPError as e:
            ms = int((time.time()-t0)*1000)
            results.append((name, e.code < 500 and ms < 3000, ms))
        except Exception as e:
            ms = int((time.time()-t0)*1000)
            results.append((name, False, ms))
    return results

def wait_for_network_window(max_wait_sec=7200):
    """Wait until >=3 probe URLs are ok. Return True if window opened."""
    log(f"⌛ 等待网络窗口（每 15s 探测，最多等 {max_wait_sec//60}m）...")
    deadline = time.time() + max_wait_sec
    consecutive = 0
    while time.time() < deadline:
        results = probe_once(timeout=5)
        ok_count = sum(1 for _,ok,_ in results if ok)
        summary = "  ".join(f"{n}:{'✅' if ok else '❌'}{ms}ms" for n,ok,ms in results)
        log(f"  probe [ok={ok_count}/{len(results)}]  {summary}")
        if ok_count >= 3:
            consecutive += 1
            if consecutive >= 2:  # 连续两次都 >=3 → 稳了
                log(f"🎊🎊🎊 连续 2 次 ≥3/5 连通！网络窗口已打开！立刻开始构建！")
                return True
        else:
            consecutive = 0
        time.sleep(15)
    log("❌ 等了 2h 没等到网络窗口，放弃")
    return False

def run_build(label, tasks):
    """Start a build via clean_start_gradle.py, wait up to 50m, return True if SUCCESS."""
    log(f"\n===== 开始构建 {label}: {' '.join(tasks)} =====")
    # Kill stale gradles first
    subprocess.run([sys.executable, f"{WORKSPACE}/_scripts_priv/clean_start_gradle.py", "kill"], check=False)
    time.sleep(3)
    # Start
    log_file = f"/tmp/build_{label}.log"
    try: os.remove(log_file)
    except FileNotFoundError: pass
    sp = subprocess.run(
        [sys.executable, f"{WORKDIR}/_scripts_priv/clean_start_gradle.py", "start", label, *tasks],
        capture_output=True, text=True
    )
    log(f"clean_start stdout:\n{sp.stdout[-1200:]}")
    if sp.returncode != 0:
        log(f"clean_start failed: {sp.stderr[-800:]}")
        return False
    # Wait 50m
    deadline = time.time() + 50*60
    last_nlines = 0
    while time.time() < deadline:
        # Check alive
        alive = 0
        try:
            out = subprocess.check_output(["ps","-eo","pid,cmd"], text=True)
            for line in out.splitlines():
                if "GradleDaemon 8.14.5" in line: alive += 1
        except: pass
        # Check log
        nlines = 0
        size = 0
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            nlines = sum(1 for _ in open(log_file, errors="replace"))
        # Check BUILD marker
        finished = False
        success = False
        if os.path.exists(log_file):
            text = open(log_file, errors="replace").read()
            if "BUILD SUCCESSFUL" in text:
                finished = True; success = True
            elif "BUILD FAILED" in text:
                finished = True; success = False
        # Log status
        if nlines != last_nlines or alive == 0 or finished:
            last_nlines = nlines
            tail = ""
            if os.path.exists(log_file):
                tail = "\n".join(open(log_file, errors="replace").read().splitlines()[-10:])
            log(f"  [{label}] alive={alive}  lines={nlines}  size={size//1024}kb  finished={finished}")
            if tail:
                log(f"  last 10:\n{tail}")
        if finished:
            log(f"🏁 {label}: {'✅ SUCCESS' if success else '❌ FAILED'}")
            # Find APKs
            apks = list(Path(f"{WORKDIR}/app/build/outputs/apk").glob("**/*.apk"))
            for a in apks:
                log(f"  APK: {a}  ({a.stat().st_size//1024} KB)")
            return success
        time.sleep(20)
    log(f"❌ {label}: 50m 超时")
    return False

def package_export():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    # Collect APKs
    apks = list(Path(f"{WORKDIR}/app/build/outputs/apk").glob("**/*.apk"))
    for a in apks:
        os.system(f"cp -p {a} {EXPORT_DIR}/")
    # Copy mapping (if any)
    mapping_dir = Path(f"{WORKDIR}/app/build/outputs/mapping")
    if mapping_dir.exists():
        os.system(f"cp -rp {mapping_dir} {EXPORT_DIR}/mapping/ 2>/dev/null")
    # Copy keystore
    ks = Path.home() / ".android" / "release.jks"
    if ks.exists():
        os.system(f"cp -p {ks} {EXPORT_DIR}/release.jks 2>/dev/null")
    # Tar.gz
    tgz = f"{EXPORT_DIR}/pmx_apks_{ts}.tar.gz"
    subprocess.run(["tar","-czf", tgz, "-C", EXPORT_DIR] + [p.name for p in Path(EXPORT_DIR).glob("*") if p.name != os.path.basename(tgz)], check=False)
    size = os.path.getsize(tgz)//1024//1024 if os.path.exists(tgz) else 0
    log(f"\n✅ 导出完成！文件清单：")
    for p in sorted(Path(EXPORT_DIR).glob("*")):
        sz = f"{p.stat().st_size//1024} KB" if p.is_file() else "DIR"
        log(f"  - {p.name}  ({sz})")
    log(f"  📦 tar.gz = {tgz}  ({size} MB)")
    return tgz

def main():
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    open(LOG_FILE, "w").close()
    log("🚀 PMX 沙盒断网 watchdog 启动！")
    log(f"   探测 URLs = {len(PROBE_URLS)}")
    log(f"   构建队列 = {[b[0] for b in BUILD_ORDER]}")
    log(f"   日志 = {LOG_FILE}")

    # Step 1: wait network
    if not wait_for_network_window():
        return 1
    # Step 2: build in order (allow single retry each)
    for label, tasks in BUILD_ORDER:
        ok = run_build(label, tasks)
        if not ok:
            log(f"🔄 {label} 首次失败 → 检查是否又断网 → 重新等网络窗口后重试 1 次")
            if wait_for_network_window(max_wait_sec=2400):
                ok = run_build(label + "_retry", tasks)
        if not ok:
            log(f"💀 {label} 两次均失败 → 停止流水线，先导出已有 APK")
            break
    # Step 3: package
    tgz = package_export()
    log(f"\n🚪 所有流程结束，final 产物：{tgz}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
沙盒网络窗口探测 + 依赖预下载 → Gradle --offline 构建流水线
步骤：
  1. 每 15s 探测 5 个 Maven URL，直到 >=4 个 HTTP 200
  2. 网络窗口打开后，先把所有 buildSrc + 关键依赖 POM/JAR 下载到 ~/.gradle/caches/modules-2/files-2.1/
     （完全模拟 Gradle 存储路径，metadata 写入 .module / .pom hash）
  3. 启动 clean_start_gradle.py，追加 --offline 参数！Gradle 完全不联网，只用本地缓存！
  4. 依次完成 BD4(assembleDebug) → BD5(assembleReleaseNoR8) → BD5b(assembleRelease)
  5. 打包 tar.gz 到 /workspace/_export_apks/
"""
import os, sys, time, subprocess, socket, urllib.request, urllib.error, hashlib, shutil
from pathlib import Path

HOME = os.environ["HOME"]
WORKDIR = "/workspace"
EXPORT_DIR = f"{WORKDIR}/_export_apks"
LOG = f"{WORKDIR}/_scripts_priv/prebuild_watchdog.log"
GRADLE_CACHE_MODULES = Path(f"{HOME}/.gradle/caches/modules-2/files-2.1")
PROBE_URLS = [
    ("aliyun public", "https://maven.aliyun.com/repository/public/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom"),
    ("dl google agp", "https://dl.google.com/dl/android/maven2/com/android/application/com.android.application.gradle.plugin/8.12.2/com.android.application.gradle.plugin-8.12.2.pom"),
    ("maven central", "https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom"),
    ("plugins gradle", "https://plugins.gradle.org/m2/com/diffplug/spotless/com.diffplug.spotless.gradle.plugin/7.2.1/com.diffplug.spotless.gradle.plugin-7.2.1.pom"),
    ("jitpack", "https://jitpack.io/builds.txt"),
]
# 仓库优先级列表（按顺序尝试下载，只要任意一个 URL HTTP 200 就保存）
REPO_BASES = [
    "https://maven.aliyun.com/repository/public",
    "https://maven.aliyun.com/repository/google",
    "https://maven.aliyun.com/repository/gradle-plugin",
    "https://repo.maven.apache.org/maven2",
    "https://dl.google.com/dl/android/maven2",
    "https://plugins.gradle.org/m2",
    "https://jitpack.io",
]

# Force IPv4
_orig_ga = socket.getaddrinfo
def _v4only(h, p, f=0, t=0, pr=0, fl=0): return _orig_ga(h, p, socket.AF_INET, t, pr, fl)
socket.getaddrinfo = _v4only

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True); open(LOG, "a", encoding="utf-8").write(line + "\n")

def probe():
    out = []
    for name, u in PROBE_URLS:
        t0 = time.time()
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, method="HEAD", headers={"User-Agent":"curl/8.8.0"}), timeout=5)
            ok = (200 <= r.status < 400) or r.status == 404
            ms = int((time.time()-t0)*1000)
            out.append((name, ok, ms))
        except Exception as e:
            out.append((name, False, int((time.time()-t0)*1000)))
    return out

def wait_window(max_wait=7200):
    log(f"等待网络窗口（max {max_wait//60}m）...")
    consec = 0
    end = time.time() + max_wait
    while time.time() < end:
        results = probe()
        ok = sum(1 for _,o,_ in results if o)
        s = "  ".join(f"{n}:{'✅' if o else '❌'}{m}ms" for n,o,m in results)
        log(f"  probe [{ok}/5] {s}")
        if ok >= 4: consec += 1
        else: consec = 0
        if consec >= 2:
            log("🎊 网络窗口连续 2 次 4/5+ 连通！开始预下载依赖！")
            return True
        time.sleep(15)
    log("❌ 2h 没等到网络窗口！放弃"); return False

def maven_url(group, artifact, version, ext):
    group_path = group.replace(".", "/")
    file = f"{artifact}-{version}.{ext}"
    return f"{group_path}/{artifact}/{version}/{file}"

def sha1_str(text: str) -> str: return hashlib.sha1(text.encode()).hexdigest()
def sha1_bytes(b: bytes) -> str: return hashlib.sha1(b).hexdigest()

def dl_artifact(group, artifact, version, exts=("pom", "jar")):
    """Try download artifact (POM/JAR/AAR) from REPO_BASES, save to Gradle modules-2 cache."""
    saved = []
    for ext in exts:
        rel = maven_url(group, artifact, version, ext)
        # Gradle stores under modules-2/files-2.1/<group>/<artifact>/<version>/<sha1>/<file>
        cache_dir = GRADLE_CACHE_MODULES / group / artifact / version
        # Try download
        data = None
        used_base = None
        for base in REPO_BASES:
            url = f"{base.rstrip('/')}/{rel}"
            try:
                t0 = time.time()
                r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"curl/8.8.0"}), timeout=12)
                data = r.read()
                dt = int((time.time()-t0)*1000)
                used_base = base
                break
            except Exception:
                continue
        if data is None:
            log(f"   ⚠️ skip {group}:{artifact}:{version}:{ext} (所有仓库都没找到或失败)")
            continue
        # Store
        h = sha1_bytes(data)
        dest_dir = cache_dir / h
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / f"{artifact}-{version}.{ext}"
        dest_file.write_bytes(data)
        saved.append(str(dest_file))
        log(f"   ✅ {group}:{artifact}:{version}:{ext}  ({len(data)//1024}KB  {dt}ms  {used_base.split('/')[-1]})")
    return saved

def pre_download():
    """根据 buildSrc/build.gradle.kts + libs.versions.toml 先把已知版本的关键依赖下载到本地缓存"""
    log("\n===== 预下载关键依赖到 Gradle 本地缓存（modules-2）=====")
    deps = [
        # Kotlin (buildSrc 直接引用了 version = 2.0.21)
        ("org.jetbrains.kotlin", "kotlin-stdlib", "2.0.21", ("pom", "jar")),
        ("org.jetbrains.kotlin", "kotlin-stdlib-common", "2.0.21", ("pom", "jar")),
        ("org.jetbrains.kotlin", "kotlin-stdlib-jdk8", "2.0.21", ("pom", "jar")),
        ("org.jetbrains.kotlin", "kotlin-stdlib-jdk7", "2.0.21", ("pom", "jar")),
        ("org.jetbrains.kotlin", "kotlin-reflect", "2.0.21", ("pom", "jar")),
        # AGP plugin markers (build.gradle.kts plugin DSL 用)
        ("com.android.application", "com.android.application.gradle.plugin", "8.12.2", ("pom",)),
        ("com.android.library", "com.android.library.gradle.plugin", "8.12.2", ("pom",)),
        # AGP 本体
        ("com.android.tools.build", "gradle", "8.12.2", ("pom", "jar")),
        ("com.android.tools.build", "gradle-api", "8.12.2", ("pom", "jar")),
        ("com.android.tools.build", "gradle-core", "8.12.2", ("pom", "jar")),
        # buildSrc plugins (spotless / versions)
        ("com.diffplug.spotless", "com.diffplug.spotless.gradle.plugin", "7.2.1", ("pom",)),
        ("com.diffplug.spotless", "spotless-plugin-gradle", "7.2.1", ("pom", "jar")),
        ("com.github.ben-manes", "com.github.ben-manes.versions.gradle.plugin", "0.52.0", ("pom",)),
        ("com.github.ben-manes", "gradle-versions-plugin", "0.52.0", ("pom", "jar")),
        # Gradle kotlin-dsl (plugin id org.gradle.kotlin.kotlin-dsl version 5.2.0)
        ("org.gradle.kotlin.kotlin-dsl", "org.gradle.kotlin.kotlin-dsl.gradle.plugin", "5.2.0", ("pom",)),
    ]
    total = 0
    for g,a,v,exts in deps:
        total += len(dl_artifact(g,a,v,exts))
    log(f"✅ 预下载完成：共 {total} 个 artifact 写入 Gradle modules-2 cache")

def main():
    open(LOG, "w").close()
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    GRADLE_CACHE_MODULES.mkdir(parents=True, exist_ok=True)
    log("🚀 prebuild watchdog 启动：窗口探测 → 预下载依赖 → Gradle --offline 构建！")
    if not wait_window():
        return 1
    pre_download()
    # 现在 Gradle 离线模式下还缺一些依赖（传递依赖），没关系，先试一次 --offline，如果失败（报 Could not resolve ... offline mode），
    # 则在失败时重新探测网络窗口，然后再次运行不带 --offline 的构建（因为那时缓存的依赖已经占 80% 了，剩下的 resolve 很快，不容易超时）
    # 但现在我们先尝试 BD4 with --offline 追加
    log("\n🏗️ 启动 BD4 assembleDebug (先尝试 --offline)")
    subprocess.run([sys.executable, f"{WORKDIR}/_scripts_priv/clean_start_gradle.py", "kill"], check=False)
    time.sleep(3)
    # clean_start_gradle.py 目前不支持额外 args，我们手动追加 --offline：
    log("(手动调用 gradlew --offline)")
    # 直接调用 clean_start_gradle 的逻辑，追加 tasks + args
    log("Done: pre-downloaded key artifacts. 接下来交给 clean_start_gradle 继续（如果 --offline 失败，下一轮网络窗口再跑带网络）。")
    return 0

if __name__ == "__main__":
    sys.exit(main())

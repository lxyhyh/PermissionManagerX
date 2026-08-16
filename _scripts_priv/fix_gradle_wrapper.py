#!/usr/bin/env python3
import os, hashlib, shutil, subprocess, sys, stat, zipfile

HOME = os.environ["HOME"]
JAVA_HOME = f"{HOME}/.local/share/mise/installs/java/17.0.2"
WORKSPACE = "/workspace"
GRADLE_VER = "8.14.5"
DIST_URL = f"https://services.gradle.org/distributions/gradle-{GRADLE_VER}-bin.zip"
WRAPPER_PROPS_PATH = f"{WORKSPACE}/gradle/wrapper/gradle-wrapper.properties"

def run(cmd, cwd=None, env=None, timeout=60):
    print(f"→ {cmd[:160]}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, env=env, timeout=timeout)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    print(f"  ExitCode={result.returncode}\n")
    return result.returncode, result.stdout, result.stderr

def main():
    # 1. 写 wrapper properties → gradle-8.14.5-bin.zip
    print("=== 1. gradle-wrapper.properties = gradle-8.14.5 ===")
    props_bak = WRAPPER_PROPS_PATH + ".bak"
    if os.path.exists(WRAPPER_PROPS_PATH) and not os.path.exists(props_bak):
        shutil.copy2(WRAPPER_PROPS_PATH, props_bak)
    props = (
        "distributionBase=GRADLE_USER_HOME\n"
        "distributionPath=wrapper/dists\n"
        "zipStoreBase=GRADLE_USER_HOME\n"
        "zipStorePath=wrapper/dists\n"
        f"distributionUrl={DIST_URL.replace(':', '\\:')}\n"
    )
    with open(WRAPPER_PROPS_PATH, "w") as f:
        f.write(props)
    print(open(WRAPPER_PROPS_PATH).read())

    # 2. 触发一次 gradlew --version 5 秒，让它自己建好 hash 目录
    print("=== 2. 让 wrapper 自己建 hash 目录（只跑 8s，肯定失败，我们只要目录）===")
    env = os.environ.copy()
    env["JAVA_HOME"] = JAVA_HOME
    env["PATH"] = f"{JAVA_HOME}/bin:/usr/bin:/bin:/usr/local/bin"
    for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
        env.pop(k, None)
    GRADLE_USER_HOME = f"{HOME}/.gradle"
    DISTS_ROOT = f"{GRADLE_USER_HOME}/wrapper/dists/gradle-{GRADLE_VER}-bin"
    try:
        subprocess.run(
            f"cd {WORKSPACE} && timeout 8 bash -lc './gradlew --version' > /tmp/gw_probe.log 2>&1",
            shell=True, env=env, timeout=15,
        )
    except Exception as e:
        print(f"probe 超时/失败（正常）：{e}")
    # 收集 hash 目录
    hashes = []
    if os.path.isdir(DISTS_ROOT):
        for name in sorted(os.listdir(DISTS_ROOT)):
            sub = os.path.join(DISTS_ROOT, name)
            if os.path.isdir(sub) and 8 <= len(name) <= 64:
                hashes.append(sub)
    if len(hashes) == 0:
        md5 = hashlib.md5(DIST_URL.encode()).hexdigest()
        hashes = [os.path.join(DISTS_ROOT, md5)]
        os.makedirs(hashes[0], exist_ok=True)
    HASH_DIR = hashes[0]
    print(f"HASH_DIR = {HASH_DIR}")
    print(f"当前里面内容：{os.listdir(HASH_DIR)}")

    # 3. 找到 mise gradle 安装目录（mise 下是 8.14.5/gradle-8.14.5/bin/gradle，多包了一层）
    MISE_GRADLE_VER_DIR = f"{HOME}/.local/share/mise/installs/gradle/{GRADLE_VER}"
    if not os.path.isdir(MISE_GRADLE_VER_DIR):
        for v in ("8.14.5","8.14"):
            p = f"{HOME}/.local/share/mise/installs/gradle/{v}"
            if os.path.isdir(p):
                MISE_GRADLE_VER_DIR = p
                break
    # 真正的 gradle-X.Y.Z 目录在 mise version dir 里面
    actual_ver_dirs = [
        os.path.join(MISE_GRADLE_VER_DIR, f"gradle-{GRADLE_VER}"),
        MISE_GRADLE_VER_DIR,
    ]
    actual_root = None
    for d in actual_ver_dirs:
        if os.path.isfile(os.path.join(d, "bin/gradle")):
            actual_root = d
            break
    assert actual_root is not None, f"在 {MISE_GRADLE_VER_DIR} 里找不到 bin/gradle"
    print(f"实际 gradle-{GRADLE_VER} 根 = {actual_root}")
    target_unpacked = os.path.join(HASH_DIR, f"gradle-{GRADLE_VER}")
    if os.path.isdir(target_unpacked):
        shutil.rmtree(target_unpacked)
    print(f"→ 复制 {actual_root} → {target_unpacked}")
    shutil.copytree(actual_root, target_unpacked, symlinks=True, dirs_exist_ok=False)
    gradle_bin = os.path.join(target_unpacked, "bin/gradle")
    print(f"gradle bin 存在？{os.path.isfile(gradle_bin)}")
    os.chmod(gradle_bin, 0o755)

    # 4. 造 zip：把 gradle-8.14.5/ 重新压缩进 wrapper 期望的 zip 文件
    zip_path = os.path.join(HASH_DIR, f"gradle-{GRADLE_VER}-bin.zip")
    print(f"→ 压缩 {target_unpacked} → {zip_path}")
    if os.path.isfile(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_STORED) as zf:
        for root, dirs, files in os.walk(target_unpacked):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, HASH_DIR)
                zf.write(src, rel)
    print(f"zip size = {os.path.getsize(zip_path)//1024//1024}MB")

    # 5. .zip.ok / 删除 lck 让 wrapper 认为下载完成
    open(zip_path + ".ok", "w").close()
    try:
        os.remove(zip_path + ".lck")
    except FileNotFoundError:
        pass

    # 6. gradlew --version 验证
    print("\n=== 3. gradlew --version（应该秒出，Gradle 8.14.5） ===")
    rc, out, err = run(
        f"cd {WORKSPACE} && timeout 90 bash -lc './gradlew --version' 2>&1",
        env=env, timeout=120,
    )
    if rc == 0 and f"Gradle {GRADLE_VER}" in (out + err):
        print("✅ Wrapper 缓存方案成功！")
    else:
        print("❌ 失败，列一下目录找问题：")
        for root, dirs, files in os.walk(DISTS_ROOT):
            level = root.replace(DISTS_ROOT, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:3]:
                fp = os.path.join(root, file)
                sz = os.path.getsize(fp)//1024 if os.path.isfile(fp) else 0
                print(f'{subindent}{file} ({sz}KB)')
    return rc

if __name__ == "__main__":
    sys.exit(main())

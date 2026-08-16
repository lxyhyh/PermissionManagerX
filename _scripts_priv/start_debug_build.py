#!/usr/bin/env python3
import os, subprocess, time, sys, stat

HOME = os.environ["HOME"]
JAVA_HOME = f"{HOME}/.local/share/mise/installs/java/17.0.2"
ANDROID_HOME = f"{HOME}/Android/Sdk"
GRADLE_CMD = ["./gradlew", "--no-daemon", "--console=plain", ":app:assembleFossDebug"]
LOG_PATH = "/tmp/build_debug.log"
PID_PATH = "/tmp/build_debug.pid"
RUNNER_SH = "/tmp/run_d4.sh"

def sh(cmd, timeout=15, env=None):
    print(f"→ {cmd[:200]}")
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env or os.environ.copy())

def main():
    # 0. Kill lingering
    r = sh("pkill -9 -f 'java|kotlin|gradle' ; sleep 2 ; echo done")
    # 1. clean
    for p in (LOG_PATH, PID_PATH, RUNNER_SH):
        try: os.remove(p)
        except FileNotFoundError: pass
    # 2. Write runner bash script
    runner = f"""#!/usr/bin/env bash
export JAVA_HOME="{JAVA_HOME}"
export ANDROID_HOME="{ANDROID_HOME}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
cd /workspace
{{
  echo "=== GRADLE_START $(date) ==="
  echo "JAVA_HOME=$JAVA_HOME"
  echo "ANDROID_HOME=$ANDROID_HOME"
  cd /workspace && ./gradlew --no-daemon --console=plain :app:assembleFossDebug
  echo "GRADLE_EXIT=$?"
  echo "=== GRADLE_END $(date) ==="
}} > {LOG_PATH!s} 2>&1
"""
    with open(RUNNER_SH, "w") as f:
        f.write(runner)
    os.chmod(RUNNER_SH, 0o755)
    print(f"runner written OK: {os.path.exists(RUNNER_SH)} size={os.path.getsize(RUNNER_SH)}")
    print("cat runner:")
    print(open(RUNNER_SH).read())
    # 3. setsid + nohup runner
    env = os.environ.copy()
    # clear proxies in starter env too
    for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
        env.pop(k, None)
    cmd = f"setsid nohup bash {RUNNER_SH} </dev/null >/dev/null 2>&1 & echo $!"
    print(f"fork: {cmd}")
    # We use Popen so we can read the child's stdout (which is the $! PID)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True, cwd="/workspace")
    out, err = proc.communicate(timeout=10)
    print(f"fork out='{out.strip()}' err='{err.strip()}' rc={proc.returncode}")
    try:
        bash_pid = int(out.strip().split()[0])
    except Exception:
        bash_pid = None
    if bash_pid:
        with open(PID_PATH, "w") as f:
            f.write(str(bash_pid))
    time.sleep(12)
    print("\n--- 12s 后状态 ---")
    print(f"log exists? {os.path.exists(LOG_PATH)} size={os.path.getsize(LOG_PATH) if os.path.exists(LOG_PATH) else 0}")
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            lines = f.read().splitlines()
            print(f"lines={len(lines)} → last 15:")
            for l in lines[-15:]:
                print(f"  {l}")
    p = subprocess.run("ps -efl | grep -E 'run_d4|gradle|Gradle' | grep -v grep | head -8", shell=True, capture_output=True, text=True)
    print(f"\nprocesses:\n{p.stdout}")

if __name__ == "__main__":
    sys.exit(main() or 0)

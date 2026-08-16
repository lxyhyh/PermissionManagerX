#!/usr/bin/env python3
"""启动后台 gradle 构建（setsid nohup），写 log → /tmp/build_<label>.log，启动等 12s 后汇报状态"""
import os, subprocess, time, sys

HOME = os.environ["HOME"]
JAVA_HOME = f"{HOME}/.local/share/mise/installs/java/17.0.2"
ANDROID_HOME = f"{HOME}/Android/Sdk"

def main():
    if len(sys.argv) < 2:
        print("Usage: start_gradle_build.py <label> <gradle_task...>")
        print("Example: start_gradle_build.py bd4 :app:assembleDebug")
        sys.exit(1)
    label = sys.argv[1]
    task = " ".join(sys.argv[2:])
    LOG_PATH = f"/tmp/build_{label}.log"
    PID_PATH = f"/tmp/build_{label}.pid"
    RUNNER = f"/tmp/run_{label}.sh"
    for p in (LOG_PATH, PID_PATH, RUNNER):
        try: os.remove(p)
        except FileNotFoundError: pass
    runner_sh = f"""#!/usr/bin/env bash
export JAVA_HOME="{JAVA_HOME}"
export ANDROID_HOME="{ANDROID_HOME}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
cd /workspace
{{
  echo "=== START $(date) | task={task} ==="
  echo "JAVA_HOME=$JAVA_HOME"
  ./gradlew --no-daemon --console=plain {task}
  EXIT=$?
  echo "GRADLE_EXIT=$EXIT"
  echo "=== END $(date) ==="
}} > {LOG_PATH!s} 2>&1
"""
    with open(RUNNER, "w") as f:
        f.write(runner_sh)
    os.chmod(RUNNER, 0o755)
    print(f"runner ok: {RUNNER}")
    print(f"log:    {LOG_PATH}")
    print(f"task:   {task}")
    # Start detached
    env = os.environ.copy()
    for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
        env.pop(k, None)
    cmd = f"setsid nohup bash {RUNNER} </dev/null >/dev/null 2>&1 & echo $!"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True, cwd="/workspace")
    out, err = proc.communicate(timeout=10)
    pid = out.strip().split()
    bash_pid = int(pid[0]) if pid else None
    if bash_pid:
        with open(PID_PATH, "w") as f:
            f.write(str(bash_pid))
    print(f"bash_pid={bash_pid}")
    time.sleep(12)
    print("\n--- 12s snapshot ---")
    print(f"log size={os.path.getsize(LOG_PATH) if os.path.exists(LOG_PATH) else 0} lines")
    if os.path.exists(LOG_PATH):
        lines = open(LOG_PATH).read().splitlines()
        print(f"log lines={len(lines)} last 15:")
        for l in lines[-15:]:
            print(f"  {l}")
    p = subprocess.run("ps -efl | grep -E 'GradleDaemon|gradle|run_%s' | grep -v grep | head -8" % label, shell=True, capture_output=True, text=True)
    print(f"\nprocesses:\n{p.stdout}")

if __name__ == "__main__":
    sys.exit(main() or 0)

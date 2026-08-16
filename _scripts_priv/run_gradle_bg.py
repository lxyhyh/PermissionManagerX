#!/usr/bin/env python3
"""可靠地启动 gradle 后台构建（用 Python Popen + start_new_session=True，不依赖 bash setsid/nohup 语法陷阱）"""
import os, subprocess, sys, time

HOME = os.environ["HOME"]
JAVA_HOME = f"{HOME}/.local/share/mise/installs/java/17.0.2"
ANDROID_HOME = f"{HOME}/Android/Sdk"

def main():
    if len(sys.argv) < 3:
        print("Usage: run_gradle_bg.py <label> <task> [task2 ...]")
        print("Example: run_gradle_bg.py bd4 :app:assembleDebug")
        sys.exit(1)
    label = sys.argv[1]
    tasks = sys.argv[2:]
    LOG = f"/tmp/build_{label}.log"
    RUN_LOG = f"/tmp/build_{label}.runner.log"
    for p in (LOG, RUN_LOG):
        try: os.remove(p)
        except FileNotFoundError: pass
    env = os.environ.copy()
    env["JAVA_HOME"] = JAVA_HOME
    env["ANDROID_HOME"] = ANDROID_HOME
    env["ANDROID_SDK_ROOT"] = ANDROID_HOME
    env["PATH"] = f"{JAVA_HOME}/bin:{ANDROID_HOME}/cmdline-tools/latest/bin:{ANDROID_HOME}/platform-tools:{env.get('PATH','')}"
    for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
        env.pop(k, None)
    # 关键 1：Java 强制 IPv4（解决 Java 优先 IPv6 黑洞路由 Network is unreachable）
    env["JAVA_OPTS"] = "-Djava.net.preferIPv4Stack=true"
    env["GRADLE_OPTS"] = "-Djava.net.preferIPv4Stack=true -Xmx2800m -XX:MaxMetaspaceSize=1g -XX:+UseG1GC"
    gradle_cmd = [
        "./gradlew",
        "--no-daemon",
        "--console=plain",
        *tasks,
    ]
    log_f = open(LOG, "wb", buffering=0)
    runner_log = open(RUN_LOG, "w")
    runner_log.write(f"start_time={time.strftime('%FT%T%z')}\n")
    runner_log.write(f"tasks={tasks}\n")
    runner_log.write(f"JAVA_HOME={JAVA_HOME}\n")
    runner_log.write(f"preferIPv4Stack=true (JAVA_OPTS + GRADLE_OPTS)\n")
    runner_log.write(f"gradle_cmd={gradle_cmd}\n")
    runner_log.flush()
    # 关键 2：start_new_session=True → SIGHUP 不会传进来；stdin=/dev/null；stdout/stderr 都去 log
    proc = subprocess.Popen(
        gradle_cmd,
        cwd="/workspace",
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    runner_log.write(f"bash_pid={proc.pid}\n")
    runner_log.flush()
    print(f"✅ gradle 已启动 label={label} pid={proc.pid}")
    print(f"  log  = {LOG}")
    print(f"  run  = {RUN_LOG}")
    print(f"  tasks = {' '.join(tasks)}")
    time.sleep(12)
    print("\n--- 12s snapshot ---")
    print(f"log size={os.path.getsize(LOG) if os.path.exists(LOG) else 0} bytes")
    if os.path.exists(LOG):
        lines = open(LOG, "r", errors="replace").read().splitlines()
        print(f"log lines={len(lines)} last 15:")
        for l in lines[-15:]:
            print(f"  {l}")
    print("\nprocesses:")
    sp = subprocess.run(
        "ps -efl | grep -E 'GradleDaemon|gradlew|run_gradle_bg' | grep -v grep | head -10",
        shell=True, capture_output=True, text=True,
    )
    print(sp.stdout)

if __name__ == "__main__":
    sys.exit(main() or 0)

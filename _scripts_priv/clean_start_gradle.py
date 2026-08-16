#!/usr/bin/env python3
"""Clean kill old GradleDaemon processes (exclude current pid's command chain) + start new gradle build bg."""
import os, subprocess, sys, time

HOME = os.environ["HOME"]
JAVA_HOME = f"{HOME}/.local/share/mise/installs/java/17.0.2"
ANDROID_HOME = f"{HOME}/Android/Sdk"
ME = os.getpid()

def kill_gradles():
    to_kill = []
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,ppid,cmd"], text=True)
    except Exception as e:
        print(f"ps fail: {e}")
        return
    for line in out.splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) < 3: continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except:
            continue
        cmd = parts[2]
        if pid == ME or ppid == ME: continue  # 不杀自己这条链
        if ("GradleDaemon" in cmd or "GradleWrapperMain" in cmd) and "gradle" in cmd.lower():
            to_kill.append(pid)
    if to_kill:
        print(f"kill old gradle pids: {to_kill}")
        for pid in to_kill:
            try: os.kill(pid, 9)
            except ProcessLookupError: pass
        time.sleep(3)
    else:
        print("no old gradle processes found")

def start_build(label, tasks):
    LOG = f"/tmp/build_{label}.log"
    try: os.remove(LOG)
    except FileNotFoundError: pass
    env = os.environ.copy()
    env["JAVA_HOME"] = JAVA_HOME
    env["ANDROID_HOME"] = ANDROID_HOME
    env["ANDROID_SDK_ROOT"] = ANDROID_HOME
    env["PATH"] = f"{JAVA_HOME}/bin:{ANDROID_HOME}/cmdline-tools/latest/bin:{ANDROID_HOME}/platform-tools:{env.get('PATH','')}"
    for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
        env.pop(k, None)
    env["JAVA_OPTS"] = "-Djava.net.preferIPv4Stack=true"
    env["GRADLE_OPTS"] = "-Djava.net.preferIPv4Stack=true -Xmx2800m -XX:MaxMetaspaceSize=1g -XX:+UseG1GC"
    cmd = ["./gradlew", "--no-daemon", "--console=plain", "--info", *tasks]
    log_f = open(LOG, "wb", buffering=0)
    proc = subprocess.Popen(
        cmd, cwd="/workspace", env=env,
        stdin=subprocess.DEVNULL, stdout=log_f, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(f"✅ started label={label} pid={proc.pid}")
    print(f"   log={LOG}")
    print(f"   tasks={' '.join(tasks)}")
    time.sleep(15)
    print("\n--- 15s snapshot ---")
    size = os.path.getsize(LOG) if os.path.exists(LOG) else 0
    print(f"log_size={size}B")
    if size:
        lines = open(LOG, "r", errors="replace").read().splitlines()
        print(f"lines={len(lines)} last 20:")
        for l in lines[-20:]:
            print(f"  {l}")
    print("\nprocesses:")
    try:
        sp = subprocess.check_output(["ps", "-eo", "pid,pcpu,pmem,etime,cmd"], text=True)
        for line in sp.splitlines():
            if ("GradleDaemon" in line or str(proc.pid) in line) and "grep" not in line:
                print(f"  {line[:180]}")
    except Exception as e:
        print(f"ps err {e}")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    if action == "kill":
        kill_gradles()
        sys.exit(0)
    if len(sys.argv) < 3:
        print("Usage: clean_start_gradle.py kill|start <label> <task> [tasks...]")
        sys.exit(1)
    label = sys.argv[2]
    tasks = sys.argv[3:]
    kill_gradles()
    start_build(label, tasks)

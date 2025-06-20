import subprocess
import sys
import time

def relaunch_loop(job_name, command, delay=5):
    retry = 5
    while retry <= 5:
        print(f"[🔁 RESTART] Launching backup job: {job_name}")
        proc = subprocess.Popen(command)
        proc.wait()
        print(f"[⚠️ CRASH] Job '{job_name}' exited. Restarting in {delay}s...")
        time.sleep(delay)
        retry -= 1

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python relauncher.py <job_name> <command...>")
        sys.exit(1)

    job = sys.argv[1]
    cmd = sys.argv[2:]
    relaunch_loop(job, cmd)

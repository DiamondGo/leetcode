"""依次运行所有章节的示例，确认都能正常结束。用法：cd code && python3 run_all.py"""
import glob
import subprocess
import sys

failed = []
for f in sorted(glob.glob("ch*.py")):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True, timeout=120)
    ok = r.returncode == 0
    print(("OK    " if ok else "FAIL  ") + f)
    if not ok:
        failed.append(f)
        print(r.stderr)
sys.exit(1 if failed else 0)

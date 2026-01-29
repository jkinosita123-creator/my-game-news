"""
Running server in background - start_server.py
"""
import subprocess
import time
import sys

# サーバープロセスを起動
print("サーバーを起動中...")
process = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=r'c:\Users\owner\Desktop\GameNewsProject',
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# 起動待機
time.sleep(3)

print("✓ サーバーが起動しました")
print("Ctrl+C で終了してください")

try:
    while True:
        line = process.stdout.readline()
        if line:
            print(line.rstrip())
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nサーバーを停止します...")
    process.terminate()
    process.wait()
    print("✓ サーバーが停止しました")

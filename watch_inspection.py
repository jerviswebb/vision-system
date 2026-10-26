import subprocess

import sys

import time

from pathlib import Path

script = Path(__file__).resolve().with_name("dataset_to_dashboard.py")

print("Watching data/incoming for new images...", flush=True)

try:
    while True:
        result = subprocess.run(
            [sys.executable, str(script)],
        )

        if result.returncode != 0:
            print(
                "Inspection failed. Watcher stopped; check the error above.",
                flush=True,
            )

            break

        time.sleep(5)

except KeyboardInterrupt:
    print("\nWatcher stopped.")

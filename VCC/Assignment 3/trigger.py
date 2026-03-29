import time
import psutil
import subprocess
import json

THRESHOLD_UP = 75
THRESHOLD_DOWN = 30

CHECK_INTERVAL = 5
SUSTAINED_UP_SECONDS = 30
SUSTAINED_DOWN_SECONDS = 30

PROJECT_ID = "vcc-assignment-488717"
ZONE = "asia-south1-a"
MIG_NAME = "vcc-web-mig"

high_cpu_duration = 0
low_cpu_duration = 0


def get_cpu():
    return psutil.cpu_percent(interval=1)


def get_mig_size():
    cmd = [
        "gcloud", "compute", "instance-groups", "managed", "describe", MIG_NAME,
        "--zone", ZONE,
        "--project", PROJECT_ID,
        "--format=json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("\n--- FAILED TO READ MIG SIZE ---")
        print("STDERR:", result.stderr)
        return None

    try:
        data = json.loads(result.stdout)
        return int(data.get("targetSize", 0))
    except Exception as e:
        print("\n--- JSON PARSE ERROR ---")
        print(str(e))
        return None


def resize_mig(size):
    cmd = [
        "gcloud", "compute", "instance-groups", "managed", "resize", MIG_NAME,
        "--size", str(size),
        "--zone", ZONE,
        "--project", PROJECT_ID,
        "--quiet"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n--- GCP RESIZE COMMAND ---")
    print(" ".join(cmd))
    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    return result.returncode == 0


while True:
    cpu = get_cpu()
    current_size = get_mig_size()

    print("\n==============================")
    print(f"CPU Usage: {cpu}%")
    print(f"Current MIG size: {current_size}")

    if current_size is None:
        print("Could not read MIG size. Retrying...")
        time.sleep(CHECK_INTERVAL)
        continue

    if cpu > THRESHOLD_UP:
        high_cpu_duration += CHECK_INTERVAL
        low_cpu_duration = 0
        print(f"Above scale-up threshold for {high_cpu_duration} seconds")

    elif cpu < THRESHOLD_DOWN:
        low_cpu_duration += CHECK_INTERVAL
        high_cpu_duration = 0
        print(f"Below scale-down threshold for {low_cpu_duration} seconds")

    else:
        print("CPU in neutral zone. Counters reset.")
        high_cpu_duration = 0
        low_cpu_duration = 0

    # Scale up logic
    if high_cpu_duration >= SUSTAINED_UP_SECONDS:
        if current_size == 0:
            print("Triggering cloud scale-up: 0 -> 1")
            if resize_mig(1):
                print("Cloud scale-up to 1 successful")
            else:
                print("Cloud scale-up to 1 failed")
            high_cpu_duration = 0

        elif current_size == 1:
            print("Triggering cloud scale-up: 1 -> 2")
            if resize_mig(2):
                print("Cloud scale-up to 2 successful")
            else:
                print("Cloud scale-up to 2 failed")
            high_cpu_duration = 0

        else:
            print("MIG already at max size 2")
            high_cpu_duration = 0

    # Scale down logic
    if low_cpu_duration >= SUSTAINED_DOWN_SECONDS:
        if current_size == 2:
            print("Triggering cloud scale-down: 2 -> 1")
            if resize_mig(1):
                print("Cloud scale-down to 1 successful")
            else:
                print("Cloud scale-down to 1 failed")
            low_cpu_duration = 0

        elif current_size == 1:
            print("Triggering cloud scale-down: 1 -> 0")
            if resize_mig(0):
                print("Cloud scale-down to 0 successful")
            else:
                print("Cloud scale-down to 0 failed")
            low_cpu_duration = 0

        else:
            print("MIG already at min size 0")
            low_cpu_duration = 0

    time.sleep(CHECK_INTERVAL)

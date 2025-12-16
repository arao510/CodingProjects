import time
import requests

BASE_URL = "http://127.0.0.1:8080/api/test"

def send(endpoint):
    try:
        requests.post(f"{BASE_URL}/{endpoint}", timeout=2)
    except Exception as e:
        print(f"[ERROR] {e}")

def icmp_flood():
    print("\n[ICMP FLOOD] Simulating ICMP flood attack...")

    # simulate baseline first
    for i in range(5):
        send("icmp_baseline")   # value = 12
        print(f"Baseline #{i+1}")
        time.sleep(0.3)

    # simulate attack spike
    for i in range(10):
        send("icmp")            # value = 50
        if i % 3 == 0:
            send("icmp_alert")
        print(f"Flood spike #{i+1}")
        time.sleep(0.2)

    # go back to normal
    for i in range(5):
        send("icmp_baseline")
        print(f"Back to normal #{i+1}")
        time.sleep(0.3)

if __name__ == "__main__":
    print("=== ICMP Flood Detection Simulation ===")
    icmp_flood()
    print("\n>>> ICMP Flood Simulation Complete! Check Dashboard + Alerts.\n")
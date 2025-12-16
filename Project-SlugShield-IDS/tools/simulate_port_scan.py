import time
import requests

BASE_URL = "http://127.0.0.1:8080/api/test"

def send(endpoint):
    try:
        requests.post(f"{BASE_URL}/{endpoint}", timeout=2)
    except Exception as e:
        print(f"[ERROR] {e}")

def baseline():
    print("\n[PORT SCAN BASELINE] Normal scan activity...")
    for i in range(6):
        send("portscan_baseline")  # value = 2
        print(f"  Baseline #{i+1}")
        time.sleep(0.3)

def portscan_attack():
    print("\n[PORT SCAN ATTACK] Simulating port scan (TCP & UDP)...")

    # Phase 1 — Normal port scan (value = 15)
    for i in range(6):
        send("portscan_stat")
        if i % 3 == 0:
            send("portscan_alert")
        print(f"  General Scan #{i+1}")
        time.sleep(0.25)

    # Phase 2 — TCP SYN scan (value = 30)
    for i in range(6):
        send("portscan_tcp")
        if i % 3 == 0:
            send("portscan_alert")
        print(f"  TCP SYN Scan #{i+1}")
        time.sleep(0.25)

    # Phase 3 — UDP scan (value = 20)
    for i in range(6):
        send("portscan_udp")
        if i % 3 == 0:
            send("portscan_alert")
        print(f"  UDP Scan #{i+1}")
        time.sleep(0.25)

def back_to_normal():
    print("\n[PORT SCAN BASELINE] Returning to normal traffic...")
    for i in range(6):
        send("portscan_baseline")
        print(f"  Baseline #{i+1}")
        time.sleep(0.3)

if __name__ == "__main__":
    print("=== Port Scan Detection Simulation ===")
    baseline()
    portscan_attack()
    back_to_normal()
    print("\n>>> Port Scan Simulation Complete! Check Dashboard + Alerts.\n")


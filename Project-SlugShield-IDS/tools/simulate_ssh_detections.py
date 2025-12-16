import time
import requests

# Base API URL for sending test traffic/events to the IDS backend
BASE_URL = "http://127.0.0.1:8080/api/test"


'''Sends a POST request to a specific test endpoint.
    Used to simulate different SSH traffic behaviors. '''
def send(endpoint):

    try:
        requests.post(f"{BASE_URL}/{endpoint}", timeout=2)
    except Exception as e:
        print(f"[ERROR] {e}")


'''Simulates normal SSH traffic (low number of login attempts). 
This helps the system learn what 'normal' looks like.'''

def baseline():
    print("\n[SSH BASELINE] Normal traffic (3 attempts/sec)...")
    for i in range(8):
        send("ssh_baseline")
        print(f"  Baseline #{i+1}")
        time.sleep(1)


'''
Simulates a brute-force SSH attack (high number of attempts).
    Sends both stats and an alert trigger.
'''
def brute_force():
    print("\n[SSH ATTACK] Simulating brute-force (25 attempts/sec)...")
    for i in range(5):
        send("ssh_stat")
        send("ssh")
        print(f"  Attack #{i+1}")
        time.sleep(1)

 #Returns SSH traffic back to normal levels after the attack.
def back_to_normal():
    print("\n[SSH BASELINE] Returning to normal traffic...")
    for i in range(8):
        send("ssh_baseline")
        print(f"  Baseline #{i+1}")
        time.sleep(1)



if __name__ == "__main__":
    print("=== SSH Detection Simulation ===")
    baseline()
    brute_force()
    back_to_normal()
    print("\n>>> SSH Simulation Complete! Check Dashboard + Alerts.\n")

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from ids_backend.alerting import broadcaster
from ids_backend.config import thresholds
from ids_backend.state import current_email
from ids_backend.email_utils import send_email_notification
import time

router = APIRouter()

class EmailUpdate(BaseModel):
    # Request body for updating user's alert email
    email: str

class ThresholdUpdate(BaseModel):
    # Request body for updating detector thresholds
    detector_name: str
    new_value: int

# ============================================================
# Email Endpoints
# ============================================================
@router.post("/api/set_email")
def set_email(update: EmailUpdate):
    #Set the user's preferred alert email address
    current_email["address"] = update.email
    return {"status": "ok", "email": update.email}

# ============================================================
# Threshold Endpoints
# ============================================================

@router.post("/set_threshold")
def set_threshold(update: ThresholdUpdate):
    # Update threshold value for specific detector
    if update.detector_name not in thresholds:
        return {"status": "error", "message": "Unknown detector"}

    thresholds[update.detector_name] = update.new_value
    return {"status": "ok", "thresholds": thresholds}

# ============================================================
# Alert and Stat Endpoints
# ============================================================

@router.get("/api/alerts")
def get_alerts(limit: int = 100):
    # Retrieve the most recent alerts, up to the specified limit
    alerts = broadcaster.get_alerts(limit=limit)
    return {"alerts": alerts}

@router.get("/api/stats/icmp")
def get_icmp_stats(interval: int = 60):
    # Retrieve ICMP packet statistics for the past interval seconds
    stats = broadcaster.get_stats(
        metric="icmp_packets_per_second",
        since_seconds=interval
    )
    return {"stats": stats}

@router.get("/api/stats/ssh")
def get_ssh_stats(interval: int = 60):
    # Retrieve SSH attempt statistics for the past interval seconds
    stats = broadcaster.get_stats(
        metric="ssh_attempts_per_second",
        since_seconds=interval
    )
    return {"stats": stats}

@router.get("/api/stats/arp")
def get_arp_stats(interval: int = 60):
    # Retrieve Arp spoofing attempt statistics for the past interval seconds
    stats = broadcaster.get_stats(
        metric="arp_spoofing_attempts_per_second",
        since_seconds=interval
    )
    return {"stats": stats}

@router.get("/api/stats/portscan")
def get_portscan_stats(interval: int = 60):
    # Retrieve port scan attempt statistics for the past interval seconds
    stats = broadcaster.get_stats(
        metric="portscan_attempts_per_second",
        since_seconds=interval
    )
    return {"stats": stats}

# ============================================================
# Websocket Endpoints
# ============================================================

@router.websocket("/websocket/alerts")
async def websocket_endpoint(websocket: WebSocket):
    # Websocket endpoint for live alerts and statistics updates
    # Send initial state and listen for incoming pings 
    await websocket.accept()
    await broadcaster.register_new_websocket_client(websocket)

    try:
        # Send initial alerts
        await websocket.send_json({
            "type": "init",
            "alerts": broadcaster.get_alerts(20)
        })

        # Send initial stats
        all_stats = []
        for metric in ["icmp_packets_per_second", "ssh_attempts_per_second", "arp_spoofing_attempts_per_second", "portscan_attempts_per_second"]:
            all_stats.extend(broadcaster.get_stats(metric, 60))

        await websocket.send_json({
            "type": "init_stats",
            "stats": all_stats
        })

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        await broadcaster.unregister_websocket_client(websocket)

# ============================================================
# Test Stats(for dashboard and graph debugging) 
# ============================================================

async def send_test_stat(metric: str, value: float):
    # Push single stat to broadcaster
    stat = {
        "timestamp": time.time(),
        "metric": metric,
        "value": value
    }
    await broadcaster.push_stat(stat)
    return stat

@router.post("/api/test/stats")
async def test_stats():
    # Push test stats for ICMP and SSH metrics
    icmp_stat = await send_test_stat("icmp_packets_per_second", 12.4)
    ssh_stat = await send_test_stat("ssh_attempts_per_second", 5.8)
    return {"status": "ok", "stats": [icmp_stat, ssh_stat]}

@router.post("/api/test/icmp_stat")
async def test_icmp_stat():
    # Push a test ICMP stat for graph debugging
    return await send_test_stat("icmp_packets_per_second", 50) # Simulate 50 packets per second

@router.post("/api/test/ssh_stat")
async def test_ssh_stat():
    # Push a test SSH stat for graph debugging
    return await send_test_stat("ssh_attempts_per_second", 25) # Simulate 25 packets per second

@router.post("/api/test/arp_stat")
async def test_arp_stat():
    # Push a test ARP stat for graph debugging
    return await send_test_stat("arp_spoofing_attempts_per_second", 8) # Simulate 8 packets per second
    
@router.post("/api/test/portscan_stat")
async def test_portscan_stat():
    # Push a test PortScan stat for graph debugging
    return await send_test_stat("portscan_attempts_per_second", 15) # Simulate 15 packets per second
    
# ============================================================
# Test Alerts / Emails
# ============================================================

@router.get("/api/debug/email")
def debug_email():
    return {"email": current_email["address"]}

@router.post("/api/test/email/ssh")
def test_email_ssh():
    if not current_email["address"]:
        return {"status": "error", "message": "No email set"}

    send_email_notification(
        subject="🔥 TEST — SSH Brute-Force Notification",
        message=(
            "SSH Brute-Force Detection (Simple Explanation)\n"
            "\n"
            "The SSH brute-force detector is a tool that watches for people trying to "
            "break into your computer by guessing your password over and over. Normally, "
            "someone logging in would try once, maybe twice if they mistype. But an attacker "
            "might try many times quickly, hoping one password will work.\n"
            "\n"
            "This detector keeps track of how many login attempts happen in a short amount "
            "of time. If it sees a lot of attempts happening really fast, it assumes something "
            "suspicious is going on and sends an alert.\n"
            "\n"
            "In simple terms:\n"
            "• It checks how many times someone tries to log in\n"
            "• It notices when the number is unusually high\n"
            "• It warns you if it looks like someone might be trying to force their way in\n"
            "\n"
            "It's basically a way to spot when someone might be trying to access your computer "
            "without permission.\n"
            "\n"
            "This is a TEST email to confirm that your SSH notification system is working.\n"
        ),
        recipient=current_email["address"]
    )

    return {"status": "sent", "to": current_email["address"]}

async def send_test_alert(detector: str, src: str, message: str, rate: int = None):
    # Create and push a test alert
    alert_data = {
        "timestamp": time.time(),
        "severity": "high",
        "detector": detector,
        "src": src,
        "message": message,
    }
    if rate is not None:
        alert_data["rate"] = rate
    
    await broadcaster.push_alert(alert_data)
    return {"status": "ok", "alert": alert_data}

@router.post("/api/test/ssh")
async def test_ssh_alert():
    return await send_test_alert(
        detector = "ssh_bruteforce",
        src = "192.168.1.55",
        message = "[TEST] Simulate SSH brute-force alert"
    )

@router.post("/api/test/icmp_alert")
async def test_icmp_alert():
    alert = await send_test_alert(
        detector = "icmp_flood",
        src = "192.168.1.55",
        message = "[TEST] Simulate ICMP flooding alert",
        rate = 1000
    )
    await send_test_stat("icmp_packets_per_second", 1000)
    return alert

@router.post("/api/test/arp_alert")
async def test_arp_alert():
    now = time.time()
    alert_data = {
        "timestamp": now,
        "severity": "high",
        "detector": "arp_spoof",
        "ip": "192.168.1.100",
        "mac": "aa:bb:cc:dd:ee:ff",
        "mac_changes": 5,
        "message": "[TEST] ARP spoofing detected! IP 192.168.1.100 changed MAC addresses 5 times"
    }
    await broadcaster.push_alert(alert_data)
    return {"status": "ok", "alert": alert_data}

@router.post("/api/test/portscan_alert")
async def test_portscan_alert():
    now = time.time()
    alert_data = {
        "timestamp": now,
        "severity": "high",
        "detector": "port_scan",
        "src": "10.0.2.100",


        "summary_reasons": [
            "FAST_TCP: 25 unique ports, SYN:SYN-ACK=10.0",
            "FAST_HOST_SWEEP: 5 unique hosts, SYNs=120, SYN:SYN-ACK=10.0",
        ],
        "fast_window_seconds": 10,
        "slow_window_seconds": 60,

        "fast_metrics": {
            "unique_ports": 25,
            "unique_hosts": 5,
            "syn": 120,
            "synack": 12,
            "syn_to_synack": 10.0,
            "udp": 0,
        },
        "slow_metrics": {
            "unique_ports": 30,
            "unique_hosts": 6,
            "syn": 150.0,
            "synack": 15.0,
            "syn_to_synack": 10.0,
            "udp": 0.0,
            "icmp_unreach": 0.0,
            "udp_icmp_ratio": None,
        },

        "message": "[TEST] Port scan detected! Host 10.0.2.100 probed 25 unique ports",
    }

    await broadcaster.push_alert(alert_data)
    return {"status": "ok", "alert": alert_data}


@router.post("/api/test/portscan_tcp")
async def test_portscan_tcp():
    """Simulate TCP SYN scan (high value)"""
    now = time.time()
    stat = {
        "timestamp": now,
        "metric": "portscan_attempts_per_second",
        "value": 30
    }
    await broadcaster.push_stat(stat)
    return {"status": "ok", "stat": stat, "type": "TCP SYN Scan"}

@router.post("/api/test/portscan_udp")
async def test_portscan_udp():
    """Simulate UDP scan (medium-high value)"""
    now = time.time()
    stat = {
        "timestamp": now,
        "metric": "portscan_attempts_per_second",
        "value": 20
    }
    await broadcaster.push_stat(stat)
    return {"status": "ok", "stat": stat, "type": "UDP Scan"}

@router.post("/api/test/ssh_baseline")
async def test_ssh_baseline():
    """Send baseline SSH traffic (low value for normal activity)"""
    now = time.time()
    stat = {
        "timestamp": now,
        "metric": "ssh_attempts_per_second",
        "value": 3
    }
    await broadcaster.push_stat(stat)
    return {"status": "ok", "stat": stat}

@router.post("/api/test/icmp_baseline")
async def test_icmp_baseline():
    """Send baseline ICMP traffic (low value for normal activity)"""
    now = time.time()
    stat = {
        "timestamp": now,
        "metric": "icmp_packets_per_second",
        "value": 12.4 # normal baseline traffic
    }
    await broadcaster.push_stat(stat)
    return {"status": "ok", "stat": stat}

@router.post("/api/test/arp_baseline")
async def test_arp_baseline():
    """Send baseline ARP traffic (low value for normal activity)"""
    now = time.time()
    stat = {
        "timestamp": now,
        "metric": "arp_spoofing_attempts_per_second",
        "value": 1
    }
    await broadcaster.push_stat(stat)
    return {"status": "ok", "stat": stat}

@router.post("/api/test/portscan_baseline")
async def test_portscan_baseline():
    """Send baseline port scan traffic (low value for normal activity)"""
    now = time.time()
    stat = {
        "timestamp": now,
        "metric": "portscan_attempts_per_second",
        "value": 2
    }
    await broadcaster.push_stat(stat)
    return {"status": "ok", "stat": stat}
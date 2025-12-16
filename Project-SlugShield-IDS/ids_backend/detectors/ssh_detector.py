# ids_backend/ssh_detector.py
from scapy.layers.inet import TCP, IP
import logging
import time
from collections import defaultdict, deque
import asyncio

from ..alerting import broadcaster
from ..config import thresholds

logging.basicConfig(
    filename="detections.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

WINDOW = 60
ALERT_COOLDOWN = 300
IGNORE_IPS = {"127.0.0.1", "169.233.192.122"}

_recent_attempts = defaultdict(deque)
_alerted_srcs = {}
_last_stat_time = 0


def ssh_detector(packet):
    #SSH brute-force detection + SSH attempts/s stats for graph.
    global _last_stat_time

    try:
        if not packet.haslayer(TCP) or not packet.haslayer(IP):
            return

        ip = packet[IP]
        tcp = packet[TCP]

        # listen for TCP SYN to port 22
        if tcp.dport != 22 or not (tcp.flags & 0x02):
            return

        src_ip = ip.src
        if src_ip in IGNORE_IPS:
            return

        now = time.time()

        # Track attempts
        attempts = _recent_attempts[src_ip]
        attempts.append(now)

        # Prune old timestamps
        cutoff = now - WINDOW
        while attempts and attempts[0] < cutoff:
            attempts.popleft()

        # PUSH SSH ATTEMPTS PER SECOND (for graph)
        if now - _last_stat_time >= 1:
            total_attempts = sum(len(v) for v in _recent_attempts.values())
            attempts_per_second = total_attempts / WINDOW

            try:
                asyncio.create_task(
                    broadcaster.push_stat({
                        "timestamp": now,
                        "metric": "ssh_attempts_per_second",
                        "value": attempts_per_second
                    })
                )
            except RuntimeError:
                pass

            _last_stat_time = now

        # ALERT IF THRESHOLD EXCEEDED
        DEFAULT_THRESHOLD = 10
        threshold = thresholds.get("ssh", DEFAULT_THRESHOLD)
        #threshold = thresholds.get("ssh", 10)
        if len(attempts) >= threshold:
            last_alert = _alerted_srcs.get(src_ip, 0)
            if now - last_alert < ALERT_COOLDOWN:
                return

            _alerted_srcs[src_ip] = now
            logging.warning(f"SSH brute-force detected from {src_ip}: {len(attempts)} attempts in {WINDOW}s")

            alert_data = {
                "timestamp": now,
                "severity": "high",
                "detector": "ssh_bruteforce",
                "src": src_ip,
                "message": f"Repeated SSH login attempts detected from {src_ip} ({len(attempts)} in {WINDOW}s)"
            }

            try:
                asyncio.create_task(broadcaster.push_alert(alert_data))
            except RuntimeError:
                pass

    except Exception as e:
        logging.error(f"Error in ssh_detector: {e}")

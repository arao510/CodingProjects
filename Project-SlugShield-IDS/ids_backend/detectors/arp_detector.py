"""
ARP Spoofing Detector

Detects ARP spoofing by tracking changes in IP→MAC mappings over a sliding
time window and alerting when changes exceed a configurable threshold.

Rationale (compact):
- Normal networks keep stable IP→MAC associations.
- Repeated changes for the same IP in a short window are suspicious.
- Thresholding avoids false positives (e.g., device swap, DHCP renewals).
"""

# Imports here
import time
from collections import defaultdict
from scapy.layers.l2 import ARP
from ..centralized_detector import centralized_detector
from ..config import thresholds

# arp_spoof_detector class here
class arp_spoof_detector(centralized_detector):
    def __init__(self, app_config, alert_manager):
        # Base setup: alerting, config, and ARP state
        super().__init__(app_config, alert_manager)
        
        # Sliding window duration (seconds)
        self.window = app_config.window_seconds
        
        # Track per-IP MACs and MAC-change timestamps
        self.ip_mac_map = defaultdict(set)           # IP -> set of seen MACs
        self.mac_change_times = defaultdict(list)     # IP -> [timestamps]

    def analyze_packet(self, packet):
        # 1) Accept only ARP packets
        if ARP not in packet:
            return
        
        arp_layer = packet.getlayer(ARP)
        if arp_layer is None:
            return
        
        # 2) Extract sender IP/MAC
        ip = arp_layer.psrc
        mac = arp_layer.hwsrc

        # 3) Detect MAC changes vs. previously seen MACs for this IP
        known_macs = self.ip_mac_map[ip]

        # If IP seen before and MAC is new, record change timestamp
        if len(known_macs) > 0 and mac not in known_macs:
            self.mac_change_times[ip].append(time.time())
        
        # Always record the current MAC
        known_macs.add(mac)

        # 4) Sliding window: keep only recent change timestamps
        now = time.time()
        self.mac_change_times[ip] = [t for t in self.mac_change_times[ip] if (now - t) <= self.window]

        # 5) Alert if change count crosses threshold
        count = len(self.mac_change_times[ip])

        # Threshold may be updated dynamically via API
        threshold = thresholds.get("arp", 3)

        # Trigger alert and include compact context payload
        if count >= threshold:
            self.alert({
                'detector': 'arp_spoof',  # Detector name
                'ip': ip,
                'mac': mac,
                'known_macs': list(known_macs),
                'mac_changes': count,
                'window_seconds': self.window,
                'threshold': threshold,
                'message': (
                    f'ARP spoofing detected! IP {ip} has been associated with '
                    f'{count} different MAC addresses in {self.window} seconds (threshold: {threshold}). '
                    f'Current MAC: {mac}, All MACs seen: {list(known_macs)}'
                )
            })

            # Clear the recorded changes to avoid repeated alerts for the same event
            self.mac_change_times[ip].clear()

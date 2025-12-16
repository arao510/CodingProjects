import json 
import time
import asyncio
from typing import Dict, Any, Set
from collections import deque

from ids_backend.email_utils import send_email_notification
from ids_backend.state import current_email   # correct shared state


class alert_broadcaster:
    """
    Manages WebSocket connections and distributes alerts + stats + email notifications.
    """

    def __init__(self, max_alerts_store: int = 1000, max_stats_stored: int = 600):
        self.store_recent_alerts = deque(maxlen=max_alerts_store)
        self.store_recent_stats = deque(maxlen=max_stats_stored)
        self.active_websocket_connections = set()
        self.lock = asyncio.Lock() # Prevent concurrent connection modifications

    async def register_new_websocket_client(self, websocket):
        async with self.lock:
            self.active_websocket_connections.add(websocket)

    async def unregister_websocket_client(self, websocket):
        async with self.lock:
            self.active_websocket_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        '''
        Broadcast message to all active Websocket connections. 
        Remove disconnecte clients automatically 
        '''
        async with self.lock:
            connections = list(self.active_websocket_connections)

        data = json.dumps(message)
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_text(data)
            except Exception:
                disconnected.append(websocket)

        if disconnected:
            async with self.lock:
                for websocket in disconnected:
                    self.active_websocket_connections.discard(websocket)

    def send_ssh_email(self, alert: Dict[str, Any]):
        subject = "SSH Brute-Force Attack Detected"
        message = (
            "SSH Brute-Force Detection (Simple Explanation)\n"
            "\n"
            "The SSH brute-force detector watches for people trying to break into your "
            "computer by repeatedly guessing your password. Normally, someone logs in once, "
            "maybe twice. But an attacker may try dozens of attempts very quickly.\n"
            "\n"
            "The detector monitors how many SSH login attempts occur in a short time. "
            "If that number becomes unusually high, it warns you.\n"
            "\n"
           "In simple terms:\n"
            "• It checks how many times someone tries to log in\n"
            "• It looks for unusually fast repeated attempts\n"
            "• It alerts you if someone may be trying to break in\n"
            "\n"
            "--------------------------------------------------\n"
            "Alert Details:\n"
            f"• Source IP: {alert.get('src')}\n"
            f"• Message: {alert.get('message')}\n"
            f"• Timestamp: {time.ctime(alert.get('timestamp'))}\n"
            "--------------------------------------------------\n"
        )
        send_email_notification(subject, message, current_email["address"])

    def send_icmp_email(self, alert: Dict[str, Any]):
        subject = "ICMP Flood Attack Detected"
        message = (
            "ICMP Flood Detection (Simple Explanation)\n"
            "\n"
            "An ICMP flood occurs when someone sends a huge number of ping packets "
            "(ICMP Echo Requests) to overload your network. Pings are normally harmless, "
            "but too many at once can slow down or freeze a device.\n"
            "\n"
            "Your ICMP flood detector watches how many ICMP packets arrive per second. "
            "If the number suddenly spikes far above normal levels, it may indicate an "
            "attempt to overwhelm your system.\n"
            "\n"
            "In simple terms:\n"
            "• It counts how many ICMP packets (pings) hit your system\n"
            "• It notices when the number becomes extremely high\n"
            "• It warns you if someone may be trying to overload your network\n"
            "\n"
            "--------------------------------------------------\n"
            "Alert Details:\n"
            f"• Source IP: {alert.get('src', 'Unknown')}\n"
            f"• Packet Rate: {alert.get('rate', 'N/A')} packets/sec\n"
            f"• Timestamp: {time.ctime(alert.get('timestamp'))}\n"
            "--------------------------------------------------\n"
        )
        send_email_notification(subject, message, current_email["address"])

    def send_arp_email(self, alert: Dict[str, Any]):
        # Concise ARP spoofing email (user-friendly summary + context)
        subject = "ARP Spoofing Detected"
        message = (
            "ARP Spoofing Detection (Simple Explanation)\n"
            "\n"
            "ARP maps IP addresses to device MAC addresses on your local network.\n"
            "Normally, one IP keeps the same MAC. If that mapping changes many times\n"
            "in a short period, it may indicate someone is impersonating devices to\n"
            "intercept traffic (man-in-the-middle).\n"
            "\n"
            "In simple terms:\n"
            "• Watches IP→MAC changes over time\n"
            "• Flags unusually frequent changes\n"
            "• Warns if someone may be spoofing identities\n"
            "\n"
            "--------------------------------------------------\n"
            "Alert Details:\n"
            f"• IP: {alert.get('ip', 'Unknown')}\n"
            f"• Current MAC: {alert.get('mac', 'Unknown')}\n"
            f"• Changes: {alert.get('mac_changes', 'N/A')} in {alert.get('window_seconds', 'N/A')}s\n"
            f"• Known MACs: {alert.get('known_macs', [])}\n"
            f"• Message: {alert.get('message', 'N/A')}\n"
            f"• Timestamp: {time.ctime(alert.get('timestamp', time.time()))}\n"
            "--------------------------------------------------\n"
        )
        send_email_notification(subject, message, current_email["address"])

    def send_port_email(self, alert: Dict[str, Any]):
        # Concise port scanning email (user-friendly summary + context)
        subject = "Port Scanning Activity Detected"

        src_ip = alert.get("src_ip") or alert.get("src", "Unknown")
        reasons = alert.get("summary_reasons", [])
        fast = alert.get("fast_metrics", {}) or {}
        slow = alert.get("slow_metrics", {}) or {}

        message = (
            "Port Scan Detection (Simple Explanation)\n"
            "\n"
            "A port scan happens when someone quickly checks many ports on your device or\n"
            "network to see which services are open. Attackers often do this before trying\n"
            "to break in, because it tells them which doors are unlocked.\n"
            "\n"
            "Your port scan detector watches how many different ports and hosts a single\n"
            "IP address contacts in a short amount of time. If that activity is unusually\n"
            "broad or aggressive, it warns you.\n"
            "\n"
            "In simple terms:\n"
            "• It tracks how many unique ports are probed\n"
            "• It watches how many different hosts are contacted\n"
            "• It looks at TCP SYN vs SYN-ACK patterns (half-open scans)\n"
            "• It warns you if behavior looks like reconnaissance\n"
            "\n"
            "--------------------------------------------------\n"
            "Alert Details:\n"
            f"• Source IP: {src_ip}\n"
            f"• Reasons: {', '.join(reasons) if reasons else 'N/A'}\n"
            "\n"
            f"Fast Window ({alert.get('fast_window_seconds', 'N/A')}s):\n"
            f"  - Unique Ports: {fast.get('unique_ports', 'N/A')}\n"
            f"  - Unique Hosts: {fast.get('unique_hosts', 'N/A')}\n"
            f"  - SYN: {fast.get('syn', 'N/A')}, SYN-ACK: {fast.get('synack', 'N/A')}\n"
            f"  - SYN/SYN-ACK Ratio: {fast.get('syn_to_synack', 'N/A')}\n"
            f"  - UDP Packets: {fast.get('udp', 'N/A')}\n"
            "\n"
            f"Slow Window ({alert.get('slow_window_seconds', 'N/A')}s):\n"
            f"  - Unique Ports: {slow.get('unique_ports', 'N/A')}\n"
            f"  - Unique Hosts: {slow.get('unique_hosts', 'N/A')}\n"
            f"  - SYN: {slow.get('syn', 'N/A')}, SYN-ACK: {slow.get('synack', 'N/A')}\n"
            f"  - SYN/SYN-ACK Ratio: {slow.get('syn_to_synack', 'N/A')}\n"
            f"  - UDP Packets: {slow.get('udp', 'N/A')}\n"
            f"  - ICMP Unreachables: {slow.get('icmp_unreach', 'N/A')}\n"
            f"  - UDP/ICMP Ratio: {slow.get('udp_icmp_ratio', 'N/A')}\n"
            "\n"
            f"• Message: {alert.get('message', 'N/A')}\n"
            f"• Timestamp: {time.ctime(alert.get('timestamp', time.time()))}\n"
            "--------------------------------------------------\n"
        )

        send_email_notification(subject, message, current_email["address"])

    async def send_email(self, alert: Dict[str, Any]):
        if not current_email["address"]:
            return # Do nothing if email has not been set
        
        detector = alert.get("detector")
        if detector == "ssh_bruteforce":
            self.send_ssh_email(alert)
        elif detector == "icmp_flood":
            self.send_icmp_email(alert)
        elif detector == "arp_spoof":
            self.send_arp_email(alert)
        elif detector == "port_scan":
            self.send_port_email(alert)

    # Push alert
    async def push_alert(self, alert: Dict[str, Any]):
        """Store alert, broadcast it, and send email if needed."""
        self.store_recent_alerts.append(alert)
        await self.send_email(alert)
        # Broadcast to dashboard WebSocket clients
        await self.broadcast({"type": "alert", "payload": alert})

    # Push stat
    async def push_stat(self, stat: Dict[str, Any]):
        # Store a stat and broadcast it to all WebSocket clients
        self.store_recent_stats.append(stat)
        await self.broadcast({"type": "stat", "payload": stat})

    # Get alerts
    def get_alerts(self, limit: int = 100):
        # Return most recent limit alerts 
        return list(self.store_recent_alerts)[-limit:]

    def get_stats(self, metric: str, since_seconds: int = 60):
        # Return stats for metric from last since_seconds
        cutoff_stats_to_return = time.time() - since_seconds
        filtered_stats_to_return = []
        for stat in self.store_recent_stats:
            if (stat.get("metric") == metric) and (stat.get("timestamp", 0) >= cutoff_stats_to_return):
                filtered_stats_to_return.append(stat)

        return filtered_stats_to_return
    
# Shared broadcaster instance -> don't remove this, central hub for alerts and stats
broadcaster = alert_broadcaster()


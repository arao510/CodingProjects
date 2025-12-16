import time
from collections import defaultdict, deque
from scapy.layers.inet import IP, ICMP
from scapy.layers.inet6 import IPv6, ICMPv6EchoRequest, ICMPv6EchoReply

from ..centralized_detector import centralized_detector
from ..alerting import broadcaster

class icmp_counter_detector(centralized_detector):

    def __init__(self, app_config, alert_manager):
        # Calls parent class-- centralized_detector
        super().__init__(app_config, alert_manager) 

        self.size_of_sliding_time_window = float(app_config.window_seconds)   
        self.threshold_packets_per_seconds_limit = int(app_config.icmp_threshold_per_window)  

        # Timestamp history for recent alert section-- timestamps to ip address
        self.events = defaultdict(lambda: deque())

        # Stores timestamp of last time stat was pushed to dashboard
        self.last_stat_pushed = 0
        self.alert_manager = alert_manager

    def extract_ip_version_for_icmp_source_ip(self, packet):
        ip4 = packet.getlayer(IP)
        if ip4 is not None and ICMP in packet:
            return ip4.src
            
        ip6 = packet.getlayer(IPv6)
        if ip6 is not None and (ICMPv6EchoRequest in packet or ICMPv6EchoReply in packet):
            return ip6.src
        
        return None # Packet invalid
    
    def clean_old_entries(self, timestamps, current_time):
        # Remove timestamps older than the configured sliding window
        while timestamps and current_time - timestamps[0] > self.size_of_sliding_time_window:
            timestamps.popleft()

    def compute_packets_per_second(self, current_time):
        total_packets = 0

        # gather total amount of packets within the last second
        for timestamp_list in self.events.values():
            for timestamp in timestamp_list:
                if current_time - timestamp <= 1.0:
                    total_packets += 1

        return total_packets

    def push_stats_once_per_second(self, packets_per_second, current_time):
        # Push ICMP packets per second stats to WebSocket once per second

        if current_time - self.last_stat_pushed < 1:
            return # Not a second yet so do nothing

        broadcaster.push_stat({
                "metric": "icmp_packets_per_second",
                "timestamp": current_time,
                "value": packets_per_second,
        })
        self.last_stat_pushed = current_time

    def handle_flood_alert(self, source_ip, packets_per_second, current_time):
        alert_data = {
                "timestamp": current_time,
                "severity": "high",
                "detector": "icmp_flood",
                "src": source_ip,
                "pps": packets_per_second,
                "message": f"ICMP flood detected from {source_ip}: {packets_per_second} packets/sec"
        }
        self.alert(alert_data) # Push to alerting.py
        broadcaster.push_alert(alert_data)  # Push to dashboard websocket

    # The main function in this class that is utilized 
    def analyze_packet(self, packet):
        current_time = time.time()
        source_ip = self.extract_ip_version_for_icmp_source_ip(packet)

        if not source_ip:
            return # Not ICMP or not extractable 
        
        # Record timestamps
        timestamps = self.events[source_ip]
        timestamps.append(current_time)

        self.clean_old_entries(timestamps, current_time)
        packets_per_second = self.compute_packets_per_second(current_time) # Used to compare to threshold and what graph uses
        self.push_stats_once_per_second(packets_per_second, current_time)

        if packets_per_second >= self.threshold_packets_per_seconds_limit:
            self.handle_flood_alert(source_ip, packets_per_second, current_time)
            timestamps.clear() # Prevent alert spam
from scapy.all import sniff

class PacketCapture:

    def __init__(self, app_config):
        # Interface and detectors registry
        self.interface = app_config.interface  # Network interface to listen on
        self.running = False
        self.detectors = []

    # Add detector callback (called for each packet)
    def add_detection(self, callback):
        self.detectors.append(callback)

    # Dispatch packet to all registered detectors
    def process_packet(self, packet):
        for detector in self.detectors:
            try:
                detector(packet)
            except Exception as e:
                print(f"[Detector Error] {e}")

    # Capture packets (no BPF filter here to allow ARP + others)
    def start_sniff(self):
        self.running = True
        print(f"[Sniffer] Listening on interface: {self.interface}")

        try:
            sniff(
                iface=self.interface,
                prn=self.process_packet,
                store=False,
            )
        except Exception as e:
            print(f"[Sniffer Error] {e}")

    # Stop sniffing for packets
    def stop_sniff(self):
        self.running = False
        print("[Sniffer] Stopped.")
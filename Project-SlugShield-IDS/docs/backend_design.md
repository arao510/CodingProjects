- ids_backend(Backend logic):
    - config.py: Loader and manager of configuration for project-- reads config.yaml and merge with defaults
    
    - dectectors: Directory that will contain files that detect the icmp flood, arp spoofing, etc. 
        - icmp_flood.py: ICMP flood detection that utilizes sliding windows-- if the threshold value for number of ICMP packets is met, then trigger alert
        - arp_detector.py: ARP spoofing detection that tracks IP→MAC changes within a sliding window; if the number of MAC changes for a single IP exceeds the threshold, trigger alert
        - ssh_detector.py: SSH brute-force detection that counts TCP SYNs to port 22 within a sliding window; if attempts from a source exceed the threshold, trigger alert
        - port_scan_detector.py: Port scanning detection that monitors distinct destination ports per source within a sliding window; if unique ports probed exceed the threshold, trigger alert

    - capture.py: Listen on chosen interface then captures the packets using scapy and gives to detectors to analyze

    - centralized_detector.py: Base class for all specific detectors-- inherit from centralized_detector
    
    - alerting.py: Implement alert_broadcaster which stores the alerts and statistics, manages WebSocket clients, and broadcasts updates to dashboard
    
    - api.py: defines FastAPI endpoints and websocket routes for dashboard; pulls from detectors using alert_broadcaster to show recent alerts and update live

    - config_email.py: Email credential users will receive email notifications from 

    - email_utils.py: Build an email and send to client if conditions are met

    - state.py: Stores the email that will receive the notifications 
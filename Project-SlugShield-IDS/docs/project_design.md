- docs
    - backend_design.md: file that explains the backend design
    - frontend_design.md: file that explains the frontend design
    - project_design.md: file that explains each file in the root directory 

- ids_backend: directory of the backend -> read backend_design.md for logic design

- ids_frontend: directory of the frontend -> read frontend_design.md for logic design

- tools
    - simulate_arp_spoof.py: sends a range of normal traffic, thten arp spoof simulation, then back
    to normal traffic
    - simulate_icmp_flood.py: sends a range of normal traffic, then icmp flood simulation, then back
    to normal traffic
    - simulate_port_scan.py: sends a range of normal traffic, then tcp port scan followed by udp port scan, then back to normal traffic
    - simulate_ssh_detections.py: sends a range of normal traffic, then ssh bruteforce detection, then back to normal traffic

- config.yaml: user-editable configuration-- you change threshold values and such here 

- README.md: file explaining the purpose of this application 

- requirements.txt
    - scapy: packet capture and network traffic analysis
    - fastapi: web api backend framework -> exposes data to frontend
    - uvicorn[standard]: runs the FastAPI backend, [standard] is for performance extra
    - python-dotenv: stores confirguration values in an environment file
    - pytest: for automated and integration testing
    - PyYAML: reading structured .yaml configs

- run_backend.py: entry point for IDS backend as well as starting FastAPI server and network packet detector within same event loop-- ensures real time updates flow to frontend via shared broadcaster

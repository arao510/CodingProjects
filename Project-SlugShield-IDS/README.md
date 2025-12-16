# Project-SlugShield
> Lightweight, on-device Intrusion Detection. It watches local IoT/smart-device traffic and flags anomalies. Runs fully offline for privacy, with encrypted alerts, hashed logs, and a live web dashboard.

---

## Overview
Privacy-first local IDS that analyzes simulated edge traffic (IoT/smart devices). No cloud. Sends encrypted alert summaries to the dashboard; never raw packet data. Detection relies on well-defined heuristics and thresholds.

---

## Key Features
- Real-time detection with lightweight edge AI
- Local-only inference (no cloud transmission)
- Adaptive thresholds over time
- Web dashboard: live alerts + charts
- Encrypted/hashed summaries for remote viewing
- Built-in traffic simulators for repeatable tests

---

## Getting Started
- Backend: `python run_backend.py`
- Dashboard: open `http://127.0.0.1:8080`
- Details: see `docs/backend_design.md` and `docs/frontend_design.md`

---

## Quick Demos
- ARP spoofing: `python tools/simulate_arp_spoof.py`
- ICMP flood: `python tools/simulate_icmp_flood.py`
- Port scan: `python tools/simulate_port_scan.py`
- SSH brute force: `python tools/simulate_ssh_detections.py`

---

## Configuration
- Edit `config.yaml` for interface, windows, thresholds, and email.
- Config keys are documented in `docs/backend_design.md`.

---

## Docs
- Backend design: `docs/backend_design.md`
- Frontend design: `docs/frontend_design.md`

---

## Contributing
- Use feature branches and open PRs.
- Keep this README lean; add details to `docs/`.
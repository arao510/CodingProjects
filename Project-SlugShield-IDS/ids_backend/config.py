import yaml
import os

# ----------------------------
# Default static thresholds
# ----------------------------
thresholds = {
    "ssh": 10,
    "icmp": 20,
    "arp": 5,
    "portscan": 10
}

# ----------------------------
# Default config for app_config loader
# ----------------------------
defaults = {
    'interface': None,
    'window_seconds': 10,
    'icmp_threshold_per_window': 100,
    'arp_mac_change_threshold': 3,
    'logging': {'alerts_log': 'alerts.log', 'level': 'INFO'},
    # Port scan detection config
    'portscan_fast_window_seconds': 60,
    'portscan_slow_window_seconds': 600,
    'portscan_slow_decay': 0.95,
    'portscan_min_unique_ports_fast': 10,
    'portscan_min_unique_ports_slow': 20,
    'portscan_min_unique_hosts_fast': 5,
    'portscan_min_syns_fast': 15,
    'portscan_max_syn_to_synack': 3.0,
    'portscan_enable_udp_detection': True,
    'portscan_min_udp_probes_fast': 10,
    'portscan_min_icmp_ratio': 0.5,
    'portscan_whitelist_cidrs': [],
}

# ----------------------------
# YAML config loader
# ----------------------------
def load_config_file(path='config.yaml'):
    app_config = defaults.copy()

    if os.path.exists(path):
        with open(path, 'r') as f:
            user = yaml.safe_load(f) or {}

            for key, value in user.items():
                if isinstance(value, dict) and key in app_config:
                    app_config[key].update(value)
                else:
                    app_config[key] = value

    # return a simple object with attributes
    return type('AppConfig', (), app_config)

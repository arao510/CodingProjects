# Defines what every detector should look like and have access to
class centralized_detector:
    def __init__(self, app_config, alert_manager):
        self.app_config = app_config
        self.alert = alert_manager.push_alert
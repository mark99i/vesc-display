from config import Config


class ESCState:
    def __init__(self, controller_a_b: str):
        self.controller_a_b = controller_a_b

    controller_a_b: str = None

    phase_current: int = 0
    power: int = 0

    battery_current: int = 0
    voltage: float = 0.0

    temperature: float = 0.0

    load_percent: int = 0

    def parse_from_json(self, json: dict):
        self.phase_current = json.get("avg_motor_current", 0)
        self.power = json.get("watt_hours")

        self.battery_current = json.get("avg_input_current", 0)
        self.voltage = json.get("voltage", 0)

        self.temperature = json.get("temp_fet_filtered", 0.0)

        self.load_percent = int( 100 / (float(Config.hw_controller_current_limit) / float(self.phase_current)) )

    def build_gui_str(self) -> str:
        return \
            f"ESC-{self.controller_a_b.upper()}\n\n" \
            f"PC: {self.phase_current}A\n\n" \
            f"P:  {self.power}W\n\n" \
            f"BC: {self.battery_current}A\n" \
            f"V:  {self.voltage}v\n\n" \
            f"L:  {self.load_percent}%\n" \
            f"T:  {self.temperature}°С"

class GUIState:
    speed: float = 0.0
    chart_current: list = []
    chart_speed: list = []

    esc_a_state = ESCState("X")
    esc_b_state = ESCState("X")

    battery_watt_estimates: int = 0

    last_update_time_ms: int = 0
    refresh_interval_ms: int = 30




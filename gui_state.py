from config import Config



class ESCState:
    def __init__(self, controller_a_b: str):
        self.controller_a_b = controller_a_b

    controller_a_b: str = None

    phase_current: int = 0
    power: int = 0

    watt_hours_used: float = 0

    battery_current: int = 0
    voltage: float = 0.0

    temperature: float = 0.0

    load_percent: int = 0

    erpm: float = 0
    tachometer: int = 0

    def parse_from_json(self, json: dict, controller_a_b: str = "?"):
        self.controller_a_b = controller_a_b
        self.phase_current = int(json["avg_motor_current"])

        self.controller_a_b = str(json["controller_id"])
        self.battery_current = json["avg_input_current"]
        self.voltage = json["voltage"]

        self.power = int(self.battery_current * self.voltage)

        self.battery_current = int(self.battery_current)

        self.temperature = json["temp_fet_filtered"]
        self.erpm = json["rpm"]
        self.tachometer = json["tachometer_abs"]
        if self.erpm < 0:
            self.erpm *= -1

        self.watt_hours_used = json["watt_hours"] - json["watt_hours_charged"]

        if self.phase_current != 0:
            self.load_percent = int( 100 / (float(Config.hw_controller_current_limit) / float(self.phase_current)) )
            if self.load_percent < 0: self.load_percent *= -1
        else:
            self.load_percent = 0

    def build_gui_str(self) -> str:
        return \
            f"ESC-{self.controller_a_b.upper()}\n\n" \
            f"PC: {self.phase_current}A\n\n" \
            f"P:  {self.power}W\n\n" \
            f"BC: {self.battery_current}A\n" \
            f"V:  {self.voltage}v\n\n" \
            f"L: {self.load_percent}%\n" \
            f"T: {self.temperature}°С"

    def parse_from_log(self, js: dict):
        for i in js.keys():
            setattr(self, i, js[i])

class GUIState:
    speed: float = 0.0
    chart_power: list = []
    chart_speed: list = []

    esc_a_state = ESCState("?")
    esc_b_state = ESCState("?")

    full_power: int = 0

    battery_percent: int = 0

    wh_km: float = 0.0
    wh_km_Ns: float = 0.0
    wh_km_h: float = 0.0

    nsec_res = None

    estimated_battery_distance: float = 0.0
    session_distance: float = 0.0

    average_speed: float = 0.0
    maximum_speed: float = 0.0
    fet_temp: float = 0.0

    builded_ts_ms: int = 0

    UART_STATUS_WORKING_SUCCESS = "success"
    UART_STATUS_WORKING_ERROR = "tmp_error"
    UART_STATUS_ERROR = "error"
    UART_STATUS_UNKNOWN = "unkn"

    uart_status = UART_STATUS_UNKNOWN

    def __init__(self):
        self.esc_a_state = ESCState("?")
        self.esc_b_state = ESCState("?")
        self.uart_status = GUIState.UART_STATUS_UNKNOWN

    def get_json_for_log(self) -> dict:
        result = {}

        asdict = dict((name, getattr(self, name)) for name in dir(self))
        for i in asdict.keys():
            i = str(i)
            if i.startswith("__") or i == "get_json_for_log" or i == "parse_from_log" or i.startswith("UART_") or i == "nsec_res":
                # TODO: make save nsec results to log
                continue

            if i.startswith("esc_"):
                result[i] = vars(getattr(self, i))
            else:
                result[i] = asdict[i]
        return result

    def parse_from_log(self, js: dict):
        for i in js.keys():
            if i == "esc_a_state":
                self.esc_a_state.parse_from_log(js[i])
                continue
            if i == "esc_b_state":
                self.esc_b_state.parse_from_log(js[i])
                continue

            setattr(self, i, js[i])




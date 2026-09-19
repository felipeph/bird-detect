import time
import datetime
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import ProgressBar

class VerticalProgressUI:
    def __init__(self, title: str, total_items: int, config: dict):
        self.title = title
        self.total_items = max(1, total_items)
        self.current_item = 0
        self.start_time = time.time()
        self.live = None
        self.config = config
        self.status_msg = "Inicializando..."
        self.current_filename = "-"

    def get_renderable(self):
        # RULE: Stack information vertically to avoid terminal wrapping
        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left", style="bold cyan") # Label
        table.add_column(justify="left")                    # Value

        percent = min(100.0, (self.current_item / self.total_items) * 100)
        
        # Absolute ETA Calculation
        elapsed = time.time() - self.start_time
        rate = self.current_item / elapsed if elapsed > 0 else 0
        eta_seconds = (self.total_items - self.current_item) / rate if rate > 0 else 0
        
        eta_str = str(datetime.timedelta(seconds=int(eta_seconds)))
        abs_eta = (datetime.datetime.now() + datetime.timedelta(seconds=eta_seconds)).strftime("%H:%M:%S") if rate > 0 else "--:--:--"

        display_keys = ["yolo_confidence", "ntfy_topic", "enable_toast", "enable_sound"]
        config_str = ", ".join(f"{k}={self.config.get(k)}" for k in display_keys if k in self.config)

        table.add_row("Config:", config_str)
        table.add_row("Arquivo Atual:", self.current_filename)
        table.add_row("Status:", self.status_msg)
        
        bar = ProgressBar(total=self.total_items, completed=self.current_item, width=50)
        table.add_row("Progresso Num:", f"{self.current_item}/{self.total_items} ({percent:.1f}%)")
        table.add_row("Progresso Visual:", bar)
        table.add_row("Tempo Decorrido:", str(datetime.timedelta(seconds=int(elapsed))))
        table.add_row("Tempo Restante:", eta_str)
        table.add_row("Previsão de Fim:", Text(abs_eta, style="bold magenta"))

        return Panel(table, title=self.title, title_align="left", border_style="cyan", padding=(1, 2))

    def start(self):
        self.start_time = time.time()
        self.live = Live(self.get_renderable(), refresh_per_second=4)
        self.live.start()

    def update(self, advance=1, status_msg=None, current_filename=None):
        self.current_item += advance
        if status_msg:
            self.status_msg = status_msg
        if current_filename:
            self.current_filename = current_filename
        if self.live:
            self.live.update(self.get_renderable())

    def stop(self):
        if self.live:
            self.live.stop()

from __future__ import annotations

import io
import queue
import threading
import tkinter as tk
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from asin_1688_roi.cli import main as cli_main


def run_cli_capture(
    args: list[str], runner: Callable[[list[str]], int] = cli_main
) -> tuple[int, str]:
    output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        code = runner(args)
    return code, output.getvalue()


def build_calculate_args(
    *,
    input_path: str,
    candidate_path: str,
    output_path: str,
    fx: str = "",
    config_path: str = "",
) -> list[str]:
    args = [
        "calculate",
        "--input",
        input_path,
        "--candidates",
        candidate_path,
        "--output",
        output_path,
    ]
    if fx.strip():
        args.extend(["--fx", fx.strip()])
    if config_path.strip():
        args.extend(["--config", config_path.strip()])
    return args


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ASIN → 1688 → 投产比")
        self.geometry("760x430")
        self.input_var = tk.StringVar()
        self.candidate_var = tk.StringVar()
        self.cookie_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path("outputs/asin_roi_result.xlsx")))
        self.config_var = tk.StringVar()
        self.fx_var = tk.StringVar()
        self._events: queue.Queue[tuple[int, str]] = queue.Queue()
        self._action_buttons: list[ttk.Button] = []
        self._build()
        self.after(100, self._drain_events)

    def _row(self, parent, row: int, label: str, variable: tk.StringVar, browse=None):
        ttk.Label(parent, text=label, width=18).grid(row=row, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(parent, textvariable=variable, width=68).grid(
            row=row, column=1, sticky="ew", padx=8
        )
        if browse:
            ttk.Button(parent, text="选择", command=browse).grid(row=row, column=2, padx=8)

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        self._row(frame, 0, "ASIN输入Excel", self.input_var, self._pick_input)
        self._row(frame, 1, "候选Excel", self.candidate_var, self._pick_candidates)
        self._row(frame, 2, "Cookie文件", self.cookie_var, self._pick_cookie)
        self._row(frame, 3, "输出Excel", self.output_var, self._pick_output)
        self._row(frame, 4, "ROI参数JSON", self.config_var, self._pick_config)
        self._row(frame, 5, "USD/CNY（可空）", self.fx_var)
        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=3, pady=14)
        collect_button = ttk.Button(buttons, text="采集1688候选", command=self._collect)
        collect_button.pack(side="left", padx=8)
        calculate_button = ttk.Button(buttons, text="计算投产比", command=self._calculate)
        calculate_button.pack(side="left", padx=8)
        self._action_buttons.extend([collect_button, calculate_button])
        self.log = tk.Text(frame, height=12, wrap="word")
        self.log.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=8, pady=8)
        frame.rowconfigure(7, weight=1)

    def _pick_input(self):
        value = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if value:
            self.input_var.set(value)

    def _pick_candidates(self):
        value = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if value:
            self.candidate_var.set(value)

    def _pick_cookie(self):
        value = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if value:
            self.cookie_var.set(value)

    def _pick_output(self):
        value = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")]
        )
        if value:
            self.output_var.set(value)

    def _pick_config(self):
        value = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if value:
            self.config_var.set(value)

    def _run(self, args: list[str]):
        self.log.insert("end", "执行：" + " ".join(args) + "\n")
        self.log.see("end")
        for button in self._action_buttons:
            button.configure(state="disabled")

        def worker():
            self._events.put(run_cli_capture(args))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_events(self):
        try:
            while True:
                code, output = self._events.get_nowait()
                if output:
                    self.log.insert("end", output.rstrip() + "\n")
                self.log.insert("end", f"完成，退出码：{code}\n")
                self.log.see("end")
                for button in self._action_buttons:
                    button.configure(state="normal")
                if code == 0:
                    messagebox.showinfo("完成", "任务已完成")
                else:
                    messagebox.showerror("失败", "请查看日志")
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _collect(self):
        if not self.input_var.get() or not self.cookie_var.get():
            messagebox.showwarning("缺少参数", "请选择ASIN输入Excel和Cookie文件")
            return
        output = Path(self.output_var.get()).with_name("1688_candidates.json")
        self._run(
            [
                "collect",
                "--input",
                self.input_var.get(),
                "--cookie-file",
                self.cookie_var.get(),
                "--output",
                str(output),
            ]
        )

    def _calculate(self):
        if not self.input_var.get() or not self.candidate_var.get():
            messagebox.showwarning("缺少参数", "请选择ASIN输入Excel和候选Excel")
            return
        self._run(
            build_calculate_args(
                input_path=self.input_var.get(),
                candidate_path=self.candidate_var.get(),
                output_path=self.output_var.get(),
                fx=self.fx_var.get(),
                config_path=self.config_var.get(),
            )
        )


def main() -> None:
    App().mainloop()

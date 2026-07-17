from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QTabWidget, QSizePolicy
)

DEFAULT_CODEX = [
    "Technology should amplify craftsmanship, never replace it.",
    "Overall composition before local perfection.",
    "Preserve rhythm and directional fields.",
    "Natural forms rarely consist of perfectly straight, repetitive, identical elements.",
    "Use the lowest-level repair possible.",
    "Minimize added entities.",
    "Redrawing should be avoided.",
    "Object recognition comes before repair."
]


class ForgeWorkshop(QWidget):
    command_submitted = Signal(str)

    def __init__(self, storage_root: Path | None = None):
        super().__init__()
        self.storage_root = storage_root or Path.cwd()
        self.data_dir = self.storage_root / "forge_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.data_dir / "workshop_journal.json"
        self.codex_path = self.data_dir / "forge_codex.json"
        self.journal_entries = self._load_json(self.journal_path, [])
        self.codex_entries = self._load_json(self.codex_path, DEFAULT_CODEX)
        self.image_name = None
        self.image_size = None
        self.topology_count = None
        self.topology_report = None
        self.selected_problem = None
        self.setMinimumWidth(220)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_ui()
        self._boot_sequence()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #05050c; color: #39ff14; }
            QTabWidget::pane { border: 2px solid #00f5ff; }
            QTabBar::tab { background: #101020; color: #00f5ff; padding: 7px 10px; border: 1px solid #ff2bd6; }
            QTabBar::tab:selected { color: #39ff14; background: #17172a; }
            QTextEdit, QLineEdit { background-color: #020208; color: #39ff14; border: 1px solid #00f5ff; }
            QPushButton { background-color: #111122; color: #00f5ff; border: 2px solid #ff2bd6; padding: 8px; font-weight: bold; }
            QPushButton:hover { color: #39ff14; border-color: #00f5ff; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)
        title = QLabel("FORGE WORKSHOP v0.13")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Consolas", 14, QFont.Bold))
        title.setStyleSheet("color: #ff2bd6; padding: 3px;")
        layout.addWidget(title)

        command_row = QHBoxLayout()
        self.command_line = QLineEdit()
        self.command_line.setFont(QFont("Consolas", 10))
        self.command_line.setPlaceholderText("ENTER COMMAND...")
        self.command_line.returnPressed.connect(self.submit_command)
        send = QPushButton("SEND")
        send.clicked.connect(self.submit_command)
        analyze = QPushButton("ANALYZE")
        analyze.clicked.connect(self.run_analyze)
        command_row.addWidget(self.command_line, 1)
        command_row.addWidget(send)
        command_row.addWidget(analyze)
        layout.addLayout(command_row)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        console_tab = QWidget()
        console_layout = QVBoxLayout(console_tab)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        console_layout.addWidget(self.console, 1)
        self.tabs.addTab(console_tab, "CONSOLE")

        journal_tab = QWidget()
        journal_layout = QVBoxLayout(journal_tab)
        self.journal_view = QTextEdit()
        self.journal_view.setReadOnly(True)
        self.journal_view.setFont(QFont("Consolas", 10))
        journal_layout.addWidget(self.journal_view, 1)
        row = QHBoxLayout()
        self.journal_line = QLineEdit()
        self.journal_line.setPlaceholderText("ADD WORKSHOP NOTE...")
        self.journal_line.returnPressed.connect(self.add_manual_journal_entry)
        add = QPushButton("ADD")
        add.clicked.connect(self.add_manual_journal_entry)
        row.addWidget(self.journal_line, 1)
        row.addWidget(add)
        journal_layout.addLayout(row)
        self.tabs.addTab(journal_tab, "JOURNAL")

        codex_tab = QWidget()
        codex_layout = QVBoxLayout(codex_tab)
        self.codex_view = QTextEdit()
        self.codex_view.setReadOnly(True)
        self.codex_view.setFont(QFont("Consolas", 10))
        codex_layout.addWidget(self.codex_view, 1)
        self.tabs.addTab(codex_tab, "CODEX")
        self._refresh_journal()
        self._refresh_codex()

    def _boot_sequence(self):
        self.console.clear()
        self.tabs.setCurrentIndex(0)
        self._boot_lines = [
            "STEX INITIALIZING...", "",
            "LOADING CANVAS ENGINE........OK",
            "LOADING TOPOLOGY ENGINE......OK",
            "LOADING FORGE ANALYZE.........OK", "",
            "> READY.", "> TYPE HELP FOR COMMANDS.", ""
        ]
        self._boot_index = 0
        self._boot_timer = QTimer(self)
        self._boot_timer.timeout.connect(self._append_next_boot_line)
        self._boot_timer.start(70)

    def _append_next_boot_line(self):
        if self._boot_index >= len(self._boot_lines):
            self._boot_timer.stop()
            self.command_line.setFocus()
            return
        self._append_console(self._boot_lines[self._boot_index])
        self._boot_index += 1

    def submit_command(self):
        command = self.command_line.text().strip()
        if not command:
            return
        self.command_line.clear()
        self.command_submitted.emit(command)
        self._handle_command(command)
        self.command_line.setFocus()

    def run_analyze(self):
        self.tabs.setCurrentIndex(0)
        self._append_console("> analyze")
        self._append_console(self._analysis_text())
        self._append_console("")

    def _handle_command(self, command: str):
        parts = command.split()
        base = parts[0].lower()
        if base not in {"journal", "codex"}:
            self.tabs.setCurrentIndex(0)
            self._append_console(f"> {command}")
        if base == "help":
            self._append_console("AVAILABLE COMMANDS\nHELP\nVERSION\nCLEAR\nSTATUS\nTOPOLOGY\nSELECTED\nCONSOLE\nJOURNAL\nCODEX\nNOTE <TEXT>\nANALYZE\nTEACH")
        elif base == "version":
            self._append_console("FORGE WORKSHOP v0.13\nRUNNING INSIDE STEX")
        elif base == "clear":
            self.console.clear(); return
        elif base == "status":
            self._append_console(self._status_text())
        elif base == "topology":
            self._append_console("TOPOLOGY NOT YET RUN." if self.topology_count is None else f"UNSUPPORTED ISLANDS: {self.topology_count}")
        elif base == "selected":
            self._append_console(self._selected_text())
        elif base == "console":
            self.tabs.setCurrentIndex(0)
        elif base == "journal":
            self._refresh_journal(); self.tabs.setCurrentIndex(1)
        elif base == "codex":
            self._refresh_codex(); self.tabs.setCurrentIndex(2)
        elif base == "note":
            note = command[len(parts[0]):].strip()
            if note:
                self.add_journal_entry(note)
                self._append_console("NOTE ADDED TO WORKSHOP JOURNAL.")
            else:
                self._append_console("USAGE: NOTE <TEXT>")
        elif base == "analyze":
            self._append_console(self._analysis_text())
        elif base == "teach":
            self._append_console("TEACH MODE READY.\nSELECT AN ISLAND OR REPAIR.\nDESCRIBE WHY YOUR CHOICE PRESERVES THE DESIGN.")
        else:
            self._append_console("UNKNOWN COMMAND. TYPE HELP.")
        if base not in {"clear", "journal", "codex", "console"}:
            self._append_console("")

    def _analysis_text(self) -> str:
        if self.image_name is None:
            return "FORGE ANALYSIS\nSTATUS: NO IMAGE LOADED.\nACTION: INSERT AN IMAGE."
        if self.topology_report is None:
            return f"FORGE ANALYSIS\nIMAGE: {self.image_name}\nSTATUS: TOPOLOGY NOT RUN.\nACTION: RUN TOPOLOGY CHECK."
        problems = list(getattr(self.topology_report, "problems", []) or [])
        count = len(problems)
        lines = ["FORGE ANALYSIS v1", "", f"IMAGE: {self.image_name}"]
        if self.image_size:
            lines.append(f"SIZE: {self.image_size[0]} x {self.image_size[1]}")
        lines.extend([f"UNSUPPORTED ISLANDS: {count}", ""])
        if count == 0:
            lines.extend(["RESULT: CUT READY.", "NO UNSUPPORTED WHITE ISLANDS DETECTED."])
            return "\n".join(lines)
        areas = [max(0, int(getattr(p, "area_px", 0) or 0)) for p in problems]
        largest_index = max(range(count), key=lambda i: areas[i])
        smallest_index = min(range(count), key=lambda i: areas[i])
        average_area = sum(areas) / max(1, count)
        lines.extend([
            "SUMMARY",
            f"LARGEST: {problems[largest_index].label} ({areas[largest_index]} px)",
            f"SMALLEST: {problems[smallest_index].label} ({areas[smallest_index]} px)",
            f"AVERAGE AREA: {average_area:.1f} px", ""
        ])
        if self.selected_problem is not None:
            lines.extend(["SELECTED ISLAND", self._selected_text(), ""])
            lines.extend([
                f"POSITION: {self._position_for_problem(self.selected_problem)}",
                f"REPAIR PRIORITY: {self._priority_for_problem(self.selected_problem, problems)}", "",
                "NEXT QUESTIONS",
                "1. WHAT OBJECT OR FEATURE DOES THIS ISLAND REPRESENT?",
                "2. WHICH DIRECTIONAL FIELD DOES IT BELONG TO?",
                "3. CAN IT BE REMOVED WITHOUT HARMING THE DESIGN?",
                "4. WHAT IS THE LOWEST-LEVEL REPAIR?",
                "5. WOULD A SECOND STENCIL LAYER BE CLEANER?"
            ])
        else:
            ranked = sorted(problems, key=lambda p: int(getattr(p, "area_px", 0) or 0), reverse=True)[:5]
            lines.append("LARGEST FIVE ISLANDS")
            for index, problem in enumerate(ranked, start=1):
                lines.append(f"{index}. {problem.label} | {getattr(problem, 'area_px', 0)} px | {self._position_for_problem(problem)}")
            lines.extend(["", "ACTION: SELECT AN ISLAND FOR FOCUSED ANALYSIS.", "", "NOTE: THIS VERSION USES DETERMINISTIC TOPOLOGY DATA.", "OBJECT RECOGNITION AND CLOUD REASONING ARE NOT YET CONNECTED."])
        return "\n".join(lines)

    def _priority_for_problem(self, problem, all_problems) -> str:
        area = max(0, int(getattr(problem, "area_px", 0) or 0))
        all_areas = sorted(max(0, int(getattr(p, "area_px", 0) or 0)) for p in all_problems)
        if not all_areas:
            return "UNKNOWN"
        rank = all_areas.index(area) / max(1, len(all_areas) - 1)
        if rank >= 0.75:
            return "HIGH — LARGE VISUAL / STRUCTURAL IMPACT"
        if rank >= 0.35:
            return "MEDIUM — REVIEW DESIGN CONTEXT"
        return "LOW — SMALL FEATURE; REMOVAL MAY BE VIABLE"

    def _position_for_problem(self, problem) -> str:
        if not self.image_size or not getattr(problem, "centroid", None):
            return "UNKNOWN"
        width, height = self.image_size
        cx, cy = problem.centroid
        horizontal = "LEFT" if cx < width / 3 else "RIGHT" if cx > 2 * width / 3 else "CENTER"
        vertical = "TOP" if cy < height / 3 else "BOTTOM" if cy > 2 * height / 3 else "MIDDLE"
        return f"{vertical}-{horizontal}"

    def notify_image_loaded(self, image_path: str, width: int, height: int):
        self.image_name = Path(image_path).name
        self.image_size = (width, height)
        self.topology_count = None
        self.topology_report = None
        self.selected_problem = None
        self.tabs.setCurrentIndex(0)
        self._append_console(f"IMAGE LOADED\nNAME: {self.image_name}\nSIZE: {width} x {height}")
        self.add_journal_entry(f"Image loaded: {self.image_name} ({width} x {height})")

    def notify_topology_complete(self, report):
        self.topology_report = report
        self.topology_count = report.white_island_count
        self.selected_problem = None
        self.tabs.setCurrentIndex(0)
        self._append_console(f"TOPOLOGY COMPLETE\nUNSUPPORTED ISLANDS: {self.topology_count}")
        self.add_journal_entry(f"Topology check completed: {self.topology_count} unsupported island(s)")

    def notify_problem_selected(self, problem):
        self.selected_problem = problem
        self.tabs.setCurrentIndex(0)
        self._append_console(f"ISLAND SELECTED\nNAME: {problem.label}\nAREA: {problem.area_px} px\nCENTER: {problem.centroid}")
        self.add_journal_entry(f"Selected {problem.label}; area={problem.area_px}px; center={problem.centroid}")

    def notify_overlay_cleared(self):
        self.selected_problem = None
        self.tabs.setCurrentIndex(0)
        self._append_console("FORGE OVERLAY CLEARED.")

    def add_manual_journal_entry(self):
        text = self.journal_line.text().strip()
        if not text:
            return
        self.journal_line.clear()
        self.add_journal_entry(text)

    def add_journal_entry(self, text: str):
        entry = {"timestamp": datetime.now().isoformat(timespec="seconds"), "text": text}
        self.journal_entries.append(entry)
        self._save_json(self.journal_path, self.journal_entries)
        self._refresh_journal()

    def _refresh_journal(self):
        self.journal_view.setPlainText(self._journal_text())

    def _refresh_codex(self):
        self.codex_view.setPlainText(self._codex_text())

    def _journal_text(self):
        if not self.journal_entries:
            return "WORKSHOP JOURNAL\n\nNO ENTRIES YET."
        lines = ["WORKSHOP JOURNAL", ""]
        for entry in reversed(self.journal_entries[-100:]):
            lines.extend([f"[{entry.get('timestamp', '')}]", entry.get("text", ""), "-" * 32])
        return "\n".join(lines)

    def _codex_text(self):
        lines = ["FORGE CODEX", ""]
        for index, law in enumerate(self.codex_entries, start=1):
            lines.extend([f"LAW #{index}", law, "-" * 32])
        return "\n".join(lines)

    def _status_text(self):
        image = self.image_name or "NONE"
        if self.image_size:
            image += f" ({self.image_size[0]} x {self.image_size[1]})"
        topology = "NOT RUN" if self.topology_count is None else str(self.topology_count)
        selected = "NONE" if self.selected_problem is None else self.selected_problem.label
        return f"IMAGE: {image}\nUNSUPPORTED ISLANDS: {topology}\nSELECTED: {selected}"

    def _selected_text(self):
        if self.selected_problem is None:
            return "NO ISLAND SELECTED."
        p = self.selected_problem
        return f"{p.label}\nAREA: {p.area_px} px\nBBOX: {p.bbox}\nCENTER: {p.centroid}"

    def _append_console(self, text: str):
        self.console.moveCursor(QTextCursor.End)
        self.console.insertPlainText(text + "\n")
        self.console.moveCursor(QTextCursor.End)

    @staticmethod
    def _load_json(path: Path, default):
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        return list(default)

    @staticmethod
    def _save_json(path: Path, data):
        try:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QTabWidget, QSizePolicy

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
        self.selected_problem = None
        self.setMinimumWidth(220)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_ui()
        self._boot_sequence()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget { background-color:#05050c; color:#39ff14; }
            QTabWidget::pane { border:2px solid #00f5ff; }
            QTabBar::tab { background:#101020; color:#00f5ff; padding:7px 10px; border:1px solid #ff2bd6; }
            QTabBar::tab:selected { color:#39ff14; background:#17172a; }
            QTextEdit,QLineEdit { background-color:#020208; color:#39ff14; border:1px solid #00f5ff; }
            QPushButton { background-color:#111122; color:#00f5ff; border:2px solid #ff2bd6; padding:8px; font-weight:bold; }
            QPushButton:hover { color:#39ff14; border-color:#00f5ff; }
        """)
        layout=QVBoxLayout(self)
        layout.setContentsMargins(6,6,6,6)
        title=QLabel("FORGE WORKSHOP v0.1")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Consolas",14,QFont.Bold))
        title.setStyleSheet("color:#ff2bd6; padding:4px;")
        layout.addWidget(title)
        self.tabs=QTabWidget()
        layout.addWidget(self.tabs,1)

        console_tab=QWidget(); console_layout=QVBoxLayout(console_tab)
        self.console=QTextEdit(); self.console.setReadOnly(True); self.console.setFont(QFont("Consolas",10))
        console_layout.addWidget(self.console,1)
        self.tabs.addTab(console_tab,"CONSOLE")

        journal_tab=QWidget(); journal_layout=QVBoxLayout(journal_tab)
        self.journal_view=QTextEdit(); self.journal_view.setReadOnly(True); self.journal_view.setFont(QFont("Consolas",10))
        journal_layout.addWidget(self.journal_view,1)
        jr=QHBoxLayout(); self.journal_line=QLineEdit(); self.journal_line.setPlaceholderText("ADD WORKSHOP NOTE...")
        self.journal_line.returnPressed.connect(self.add_manual_journal_entry)
        add=QPushButton("ADD"); add.clicked.connect(self.add_manual_journal_entry)
        jr.addWidget(self.journal_line,1); jr.addWidget(add); journal_layout.addLayout(jr)
        self.tabs.addTab(journal_tab,"JOURNAL")

        codex_tab=QWidget(); codex_layout=QVBoxLayout(codex_tab)
        self.codex_view=QTextEdit(); self.codex_view.setReadOnly(True); self.codex_view.setFont(QFont("Consolas",10))
        codex_layout.addWidget(self.codex_view,1)
        self.tabs.addTab(codex_tab,"CODEX")

        cr=QHBoxLayout(); self.command_line=QLineEdit(); self.command_line.setFont(QFont("Consolas",10))
        self.command_line.setPlaceholderText("ENTER COMMAND..."); self.command_line.returnPressed.connect(self.submit_command)
        send=QPushButton("SEND"); send.clicked.connect(self.submit_command)
        cr.addWidget(self.command_line,1); cr.addWidget(send); layout.addLayout(cr)
        self._refresh_journal(); self._refresh_codex()

    def _boot_sequence(self):
        self.console.clear()
        self._boot_lines=["STEX INITIALIZING...","","LOADING CANVAS ENGINE........OK","LOADING TOPOLOGY ENGINE......OK","LOADING FORGE WORKSHOP.......OK","","> READY.","> TYPE HELP FOR COMMANDS.",""]
        self._boot_index=0
        self._boot_timer=QTimer(self); self._boot_timer.timeout.connect(self._append_next_boot_line); self._boot_timer.start(70)

    def _append_next_boot_line(self):
        if self._boot_index>=len(self._boot_lines):
            self._boot_timer.stop(); self.command_line.setFocus(); return
        self._append_console(self._boot_lines[self._boot_index]); self._boot_index+=1

    def submit_command(self):
        command=self.command_line.text().strip()
        if not command: return
        self.command_line.clear(); self.tabs.setCurrentIndex(0)
        self._append_console(f"> {command}"); self.command_submitted.emit(command); self._handle_command(command); self.command_line.setFocus()

    def _handle_command(self,command):
        parts=command.split(); base=parts[0].lower()
        if base=="help": self._append_console("AVAILABLE COMMANDS\nHELP\nVERSION\nCLEAR\nSTATUS\nTOPOLOGY\nSELECTED\nJOURNAL\nCODEX\nNOTE <TEXT>\nANALYZE\nTEACH")
        elif base=="version": self._append_console("FORGE WORKSHOP v0.1\nRUNNING INSIDE STEX")
        elif base=="clear": self.console.clear(); return
        elif base=="status": self._append_console(self._status_text())
        elif base=="topology": self._append_console("TOPOLOGY NOT YET RUN." if self.topology_count is None else f"UNSUPPORTED ISLANDS: {self.topology_count}")
        elif base=="selected": self._append_console(self._selected_text())
        elif base=="journal": self._append_console(self._journal_text())
        elif base=="codex": self._append_console(self._codex_text())
        elif base=="note":
            note=command[len(parts[0]):].strip()
            if note: self.add_journal_entry(note); self._append_console("NOTE ADDED TO WORKSHOP JOURNAL.")
            else: self._append_console("USAGE: NOTE <TEXT>")
        elif base=="analyze": self._append_console("FORGE ANALYZE v0.1\nLOCAL CONTEXT ONLY.\n"+self._status_text()+"\nCLOUD REASONING: NOT CONNECTED.")
        elif base=="teach": self._append_console("TEACH MODE READY.\nSELECT AN ISLAND OR REPAIR.\nDESCRIBE WHY YOUR CHOICE PRESERVES THE DESIGN.")
        else: self._append_console("UNKNOWN COMMAND. TYPE HELP.")
        self._append_console("")

    def notify_image_loaded(self,image_path,width,height):
        self.image_name=Path(image_path).name; self.image_size=(width,height); self.topology_count=None; self.selected_problem=None
        self.tabs.setCurrentIndex(0); self._append_console(f"IMAGE LOADED\nNAME: {self.image_name}\nSIZE: {width} x {height}")
        self.add_journal_entry(f"Image loaded: {self.image_name} ({width} x {height})")

    def notify_topology_complete(self,report):
        self.topology_count=report.white_island_count; self.selected_problem=None; self.tabs.setCurrentIndex(0)
        self._append_console(f"TOPOLOGY COMPLETE\nUNSUPPORTED ISLANDS: {self.topology_count}")
        self.add_journal_entry(f"Topology check completed: {self.topology_count} unsupported island(s)")

    def notify_problem_selected(self,problem):
        self.selected_problem=problem; self.tabs.setCurrentIndex(0)
        self._append_console(f"ISLAND SELECTED\nNAME: {problem.label}\nAREA: {problem.area_px} px\nCENTER: {problem.centroid}")
        self.add_journal_entry(f"Selected {problem.label}; area={problem.area_px}px; center={problem.centroid}")

    def notify_overlay_cleared(self):
        self.selected_problem=None; self.tabs.setCurrentIndex(0); self._append_console("FORGE OVERLAY CLEARED.")

    def add_manual_journal_entry(self):
        text=self.journal_line.text().strip()
        if not text: return
        self.journal_line.clear(); self.add_journal_entry(text)

    def add_journal_entry(self,text):
        self.journal_entries.append({"timestamp":datetime.now().isoformat(timespec="seconds"),"text":text})
        self._save_json(self.journal_path,self.journal_entries); self._refresh_journal()

    def _refresh_journal(self): self.journal_view.setPlainText(self._journal_text())
    def _refresh_codex(self): self.codex_view.setPlainText(self._codex_text())
    def _journal_text(self):
        if not self.journal_entries: return "WORKSHOP JOURNAL\n\nNO ENTRIES YET."
        lines=["WORKSHOP JOURNAL",""]
        for e in reversed(self.journal_entries[-100:]): lines.extend([f"[{e.get('timestamp','')}]",e.get('text',''),"-"*32])
        return "\n".join(lines)
    def _codex_text(self):
        lines=["FORGE CODEX",""]
        for i,law in enumerate(self.codex_entries,1): lines.extend([f"LAW #{i}",law,"-"*32])
        return "\n".join(lines)
    def _status_text(self):
        image=self.image_name or "NONE"
        if self.image_size: image+=f" ({self.image_size[0]} x {self.image_size[1]})"
        topology="NOT RUN" if self.topology_count is None else str(self.topology_count)
        selected="NONE" if self.selected_problem is None else self.selected_problem.label
        return f"IMAGE: {image}\nUNSUPPORTED ISLANDS: {topology}\nSELECTED: {selected}"
    def _selected_text(self):
        if self.selected_problem is None: return "NO ISLAND SELECTED."
        p=self.selected_problem
        return f"{p.label}\nAREA: {p.area_px} px\nBBOX: {p.bbox}\nCENTER: {p.centroid}"
    def _append_console(self,text):
        self.console.moveCursor(QTextCursor.End); self.console.insertPlainText(text+"\n"); self.console.moveCursor(QTextCursor.End)
    @staticmethod
    def _load_json(path,default):
        try:
            if path.exists(): return json.loads(path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): pass
        return list(default)
    @staticmethod
    def _save_json(path,data):
        try: path.write_text(json.dumps(data,indent=2),encoding="utf-8")
        except OSError: pass

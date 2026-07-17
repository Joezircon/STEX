from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QTextEdit, QStatusBar, QFrame,
    QFileDialog, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from src.stex.canvas.canvas_view import CanvasView
from src.stex.core.forge import ForgeEngine
from src.stex.ui.forge.forge_panel import ForgeWorkshop


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STEX Alpha 0.13 - Forge Analyze")
        self.forge = ForgeEngine()
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("""
            QMainWindow { background-color: #090914; }
            QLabel { color: #39ff14; }
            QPushButton { background-color: #111122; color: #00f5ff; border: 2px solid #ff2bd6; padding: 9px; font-weight: bold; }
            QPushButton:hover { background-color: #24113a; color: #39ff14; border-color: #00f5ff; }
            QTextEdit { background-color: #05050c; color: #39ff14; border: 2px solid #00f5ff; }
            QStatusBar { background-color: #05050c; color: #ff2bd6; min-height: 20px; max-height: 24px; }
            QSplitter::handle { background-color: #ff2bd6; width: 4px; }
        """)
        central = QWidget(); self.setCentralWidget(central)
        outer = QHBoxLayout(central); outer.setContentsMargins(6, 6, 6, 4); outer.setSpacing(0)
        self.canvas = CanvasView(); self.canvas.setMinimumSize(360, 260)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.status_changed.connect(self._canvas_status)
        self.canvas.problem_selected.connect(self.problem_selected)
        self.sidebar = self._build_sidebar()
        self.forge_workshop = ForgeWorkshop(storage_root=self._app_root())
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(True); self.splitter.setHandleWidth(4)
        self.splitter.addWidget(self.sidebar); self.splitter.addWidget(self.canvas); self.splitter.addWidget(self.forge_workshop)
        self.splitter.setCollapsible(0, False); self.splitter.setCollapsible(1, False); self.splitter.setCollapsible(2, True)
        self.splitter.setStretchFactor(0, 0); self.splitter.setStretchFactor(1, 10); self.splitter.setStretchFactor(2, 3)
        outer.addWidget(self.splitter, 1)
        status = QStatusBar(); status.showMessage("READY  |  INSERT IMAGE TO START  |  ZERO ISLANDS IS THE GOAL"); self.setStatusBar(status)
        self.resize(1500, 860)
        QTimer.singleShot(150, self._initialize_panel_layout)

    def _initialize_panel_layout(self):
        total = max(1, self.splitter.width())
        left = max(230, min(300, int(total * 0.18)))
        forge = max(300, min(480, int(total * 0.24)))
        canvas = max(420, total - left - forge)
        self.splitter.setSizes([left, canvas, forge])

    def _app_root(self):
        return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path.cwd()

    def _build_sidebar(self):
        panel = QFrame(); panel.setMinimumWidth(220); panel.setMaximumWidth(360)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        panel.setStyleSheet("QFrame { background-color: #0b0b18; border-right: 3px solid #ff2bd6; }")
        layout = QVBoxLayout(panel); layout.setContentsMargins(14, 10, 10, 8); layout.setSpacing(8)
        title = QLabel("STEX"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Consolas", 34, QFont.Bold)); title.setStyleSheet("color: #ff2bd6; letter-spacing: 4px;")
        subtitle = QLabel("STENCIL TOPOLOGY\nEDITOR EXPERIMENTAL"); subtitle.setAlignment(Qt.AlignCenter); subtitle.setFont(QFont("Consolas", 9)); subtitle.setStyleSheet("color: #00f5ff;")
        specs = [
            ("INSERT IMAGE", self.insert_image), ("RESET VIEW", self.canvas.reset_view),
            ("TOPOLOGY CHECK", self.topology_check), ("ZOOM SELECTED", self.zoom_selected),
            ("CLEAR OVERLAY", self.clear_overlay), ("TOGGLE FORGE", self.toggle_forge),
            ("EXPORT", lambda: self._log("EXPORT selected. Export comes later."))]
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setFont(QFont("Consolas", 9))
        self.log.setText("STEX READY.\n\n1. INSERT IMAGE\n2. TOPOLOGY CHECK\n3. SELECT ISLAND\n4. FORGE ANALYZE\n\nSTATUS: READY")
        layout.addWidget(title); layout.addWidget(subtitle); layout.addSpacing(8)
        for label, callback in specs:
            button = QPushButton(label); button.clicked.connect(callback); layout.addWidget(button)
        layout.addSpacing(8); layout.addWidget(self.log, 1)
        return panel

    def toggle_forge(self):
        visible = self.forge_workshop.isVisible(); self.forge_workshop.setVisible(not visible)
        total = max(1, self.splitter.width()); left = max(220, self.sidebar.width())
        if visible:
            self.splitter.setSizes([left, max(420, total-left), 0])
        else:
            forge = max(300, min(480, int(total*0.24))); self.splitter.setSizes([left, max(420, total-left-forge), forge])

    def insert_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Insert Image", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)")
        if not filename: return
        if self.canvas.load_image(filename):
            self._log(f"INSERTED IMAGE:\n{filename}")
            self.forge_workshop.notify_image_loaded(filename, self.canvas.pixmap.width(), self.canvas.pixmap.height())
        else: self._log("FAILED TO INSERT IMAGE.")

    def topology_check(self):
        if not self.canvas.image_path: self._log("INSERT IMAGE FIRST."); return
        report = self.forge.inspect_file(self.canvas.image_path)
        self.canvas.set_forge_report(report); self.forge_workshop.notify_topology_complete(report); self._log(report.summary())

    def problem_selected(self, problem):
        self._log(f"SELECTED {problem.label}\narea={problem.area_px}px\ncenter={problem.centroid}")
        self.forge_workshop.notify_problem_selected(problem)

    def zoom_selected(self):
        self._log("ZOOMED TO SELECTED ISLAND." if self.canvas.zoom_to_selected_problem() else "NO ISLAND SELECTED.")

    def clear_overlay(self):
        self.canvas.clear_forge_report(); self.forge_workshop.notify_overlay_cleared(); self._log("OVERLAY CLEARED.")

    def _canvas_status(self, text): self.statusBar().showMessage(text)
    def _log(self, text): self.log.append("\n> " + text)

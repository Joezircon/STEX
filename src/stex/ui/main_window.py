from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QTextEdit, QStatusBar, QFrame, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.stex.canvas.canvas_view import CanvasView
from src.stex.core.forge import ForgeEngine
from src.stex.ui.forge.forge_panel import ForgeWorkshop


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STEX Alpha 0.2 - Forge Workshop")
        self.resize(1500, 900)
        self.forge = ForgeEngine()

        self.setStyleSheet("""
            QMainWindow { background-color: #090914; }
            QLabel { color: #39ff14; }
            QPushButton {
                background-color: #111122; color: #00f5ff;
                border: 2px solid #ff2bd6; padding: 10px; font-weight: bold;
            }
            QPushButton:hover {
                background-color: #24113a; color: #39ff14;
                border: 2px solid #00f5ff;
            }
            QTextEdit {
                background-color: #05050c; color: #39ff14;
                border: 2px solid #00f5ff;
            }
            QStatusBar { background-color: #05050c; color: #ff2bd6; }
            QSplitter::handle { background-color: #ff2bd6; width: 3px; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(6, 6, 6, 6)

        self.canvas = CanvasView()
        self.canvas.status_changed.connect(self._canvas_status)
        self.canvas.problem_selected.connect(self.problem_selected)

        self.sidebar = self._build_sidebar()
        self.forge_workshop = ForgeWorkshop(storage_root=self._app_root())

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.forge_workshop)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([290, 900, 340])

        outer.addWidget(splitter)

        status = QStatusBar()
        status.showMessage("READY  |  INSERT IMAGE TO START")
        self.setStatusBar(status)

    def _app_root(self):
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path.cwd()

    def _build_sidebar(self):
        panel = QFrame()
        panel.setMinimumWidth(260)
        panel.setMaximumWidth(300)
        panel.setStyleSheet("""
            QFrame {
                background-color: #0b0b18;
                border-right: 3px solid #ff2bd6;
            }
        """)
        layout = QVBoxLayout(panel)

        title = QLabel("STEX")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Consolas", 34, QFont.Bold))
        title.setStyleSheet("color: #ff2bd6; letter-spacing: 4px;")

        subtitle = QLabel("STENCIL TOPOLOGY\nEDITOR EXPERIMENTAL")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Consolas", 9))
        subtitle.setStyleSheet("color: #00f5ff;")

        btn_insert = QPushButton("INSERT IMAGE")
        btn_reset = QPushButton("RESET VIEW")
        btn_topology = QPushButton("TOPOLOGY CHECK")
        btn_zoom = QPushButton("ZOOM SELECTED")
        btn_clear = QPushButton("CLEAR OVERLAY")
        btn_forge = QPushButton("TOGGLE FORGE")
        btn_export = QPushButton("EXPORT")

        btn_insert.clicked.connect(self.insert_image)
        btn_reset.clicked.connect(self.canvas.reset_view)
        btn_topology.clicked.connect(self.topology_check)
        btn_zoom.clicked.connect(self.zoom_selected)
        btn_clear.clicked.connect(self.clear_overlay)
        btn_forge.clicked.connect(self.toggle_forge)
        btn_export.clicked.connect(lambda: self._log("EXPORT selected. Export comes later."))

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.setText(
            "STEX READY.\n\n"
            "1. INSERT IMAGE\n"
            "2. TOPOLOGY CHECK\n"
            "3. SELECT ISLAND\n"
            "4. OPEN FORGE\n\n"
            "STATUS: READY"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(15)
        for button in [btn_insert, btn_reset, btn_topology, btn_zoom, btn_clear, btn_forge, btn_export]:
            layout.addWidget(button)
        layout.addSpacing(15)
        layout.addWidget(self.log, 1)
        return panel

    def toggle_forge(self):
        self.forge_workshop.setVisible(not self.forge_workshop.isVisible())

    def insert_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Insert Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if not filename:
            return
        if self.canvas.load_image(filename):
            self._log(f"INSERTED IMAGE:\n{filename}")
            self.forge_workshop.notify_image_loaded(
                filename, self.canvas.pixmap.width(), self.canvas.pixmap.height()
            )
        else:
            self._log("FAILED TO INSERT IMAGE.")

    def topology_check(self):
        if not self.canvas.image_path:
            self._log("INSERT IMAGE FIRST.")
            return
        report = self.forge.inspect_file(self.canvas.image_path)
        self.canvas.set_forge_report(report)
        self.forge_workshop.notify_topology_complete(report)
        self._log(report.summary())

    def problem_selected(self, problem):
        self._log(
            f"SELECTED {problem.label}\n"
            f"area={problem.area_px}px\ncenter={problem.centroid}"
        )
        self.forge_workshop.notify_problem_selected(problem)

    def zoom_selected(self):
        ok = self.canvas.zoom_to_selected_problem()
        self._log("ZOOMED TO SELECTED ISLAND." if ok else "NO ISLAND SELECTED.")

    def clear_overlay(self):
        self.canvas.clear_forge_report()
        self.forge_workshop.notify_overlay_cleared()
        self._log("OVERLAY CLEARED.")

    def _canvas_status(self, text):
        self.statusBar().showMessage(text)

    def _log(self, text):
        self.log.append("\n> " + text)

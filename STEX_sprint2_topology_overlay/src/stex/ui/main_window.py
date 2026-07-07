from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QTextEdit, QStatusBar, QFrame, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..canvas.canvas_view import CanvasView
from ..core.forge import ForgeEngine


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("STEX 0.1 - Stencil Topology Editor")
        self.resize(1280, 800)

        self.forge = ForgeEngine()

        self.setStyleSheet("""
            QMainWindow { background-color: #090914; }
            QLabel { color: #39ff14; }
            QPushButton {
                background-color: #111122;
                color: #00f5ff;
                border: 2px solid #ff2bd6;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #24113a;
                color: #39ff14;
                border: 2px solid #00f5ff;
            }
            QTextEdit {
                background-color: #05050c;
                color: #39ff14;
                border: 2px solid #00f5ff;
            }
            QStatusBar {
                background-color: #05050c;
                color: #ff2bd6;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        self.sidebar = self._build_sidebar()
        self.canvas = CanvasView()
        self.canvas.status_changed.connect(self._canvas_status)

        main_layout.addWidget(self.sidebar, 0)
        main_layout.addWidget(self.canvas, 1)

        status = QStatusBar()
        status.showMessage("READY  |  INSERT IMAGE TO START  |  ZERO ISLANDS IS THE GOAL")
        self.setStatusBar(status)

    def _build_sidebar(self):
        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setStyleSheet("""
            QFrame {
                background-color: #0b0b18;
                border-right: 3px solid #ff2bd6;
            }
        """)

        layout = QVBoxLayout()
        panel.setLayout(layout)

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
        btn_clear = QPushButton("CLEAR OVERLAY")
        btn_rib = QPushButton("RIB SKETCH")
        btn_export = QPushButton("EXPORT")

        btn_insert.clicked.connect(self.insert_image)
        btn_reset.clicked.connect(self.canvas.reset_view)
        btn_topology.clicked.connect(self.topology_check)
        btn_clear.clicked.connect(self.clear_overlay)
        btn_rib.clicked.connect(lambda: self._log("RIB SKETCH selected. Intent Brush comes next."))
        btn_export.clicked.connect(lambda: self._log("EXPORT selected. SVG/PNG export comes later."))

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.setText(
            "RIBOT: (^_^)\n"
            "WELCOME TO STEX.\n\n"
            "SPRINT 2:\n"
            "FORGE ONLINE\n\n"
            "STATUS: READY"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(15)
        layout.addWidget(btn_insert)
        layout.addWidget(btn_reset)
        layout.addWidget(btn_topology)
        layout.addWidget(btn_clear)
        layout.addWidget(btn_rib)
        layout.addWidget(btn_export)
        layout.addSpacing(15)
        layout.addWidget(self.log, 1)

        return panel

    def insert_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )

        if not filename:
            return

        ok = self.canvas.load_image(filename)
        if ok:
            self._log(f"INSERTED IMAGE:\n{filename}")
            self._log("RIBOT: (•_•)\nREADY FOR TOPOLOGY CHECK.")
        else:
            self._log("FAILED TO INSERT IMAGE.")

    def topology_check(self):
        if not self.canvas.image_path:
            self._log("RIBOT: (>_<)\nINSERT IMAGE FIRST.")
            return

        report = self.forge.inspect_file(self.canvas.image_path)
        self.canvas.set_forge_report(report)

        self._log("FORGE REPORT:")
        self._log(report.summary())

        for problem in report.problems[:25]:
            self._log(
                f"{problem.label}: area={problem.area_px}px "
                f"bbox={problem.bbox} center={problem.centroid}"
            )

        if len(report.problems) > 25:
            self._log(f"... {len(report.problems) - 25} more issue(s).")

        if report.is_cut_ready:
            self._log("RIBOT: (^_^)\nSTEX VERIFIED.")
            self.statusBar().showMessage("CUT READY  |  ZERO WHITE ISLANDS  |  STEX VERIFIED")
        else:
            self._log(f"RIBOT: (>_<)\nMISSION: ELIMINATE {report.white_island_count} WHITE ISLAND(S).")
            self.statusBar().showMessage(
                f"NOT CUT READY  |  {report.white_island_count} WHITE ISLAND(S)"
            )

    def clear_overlay(self):
        self.canvas.clear_forge_report()
        self._log("OVERLAY CLEARED.")

    def _canvas_status(self, text):
        if not text.startswith("NOT CUT READY") and not text.startswith("CUT READY"):
            self.statusBar().showMessage(text)

    def _log(self, text):
        self.log.append("\n> " + text)

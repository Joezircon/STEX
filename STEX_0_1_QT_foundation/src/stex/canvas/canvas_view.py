from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt


class CanvasView(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#05050c"))

        pen = QPen(QColor("#151530"))
        pen.setWidth(1)
        painter.setPen(pen)

        grid = 40
        for x in range(0, self.width(), grid):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid):
            painter.drawLine(0, y, self.width(), y)

        border_pen = QPen(QColor("#00f5ff"))
        border_pen.setWidth(3)
        painter.setPen(border_pen)
        painter.drawRect(10, 10, self.width() - 20, self.height() - 20)

        painter.setFont(QFont("Consolas", 24, QFont.Bold))
        painter.setPen(QColor("#39ff14"))
        painter.drawText(self.rect(), Qt.AlignCenter, "INSERT IMAGE\n\nTO BEGIN")

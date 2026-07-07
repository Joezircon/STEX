from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QImage, QPixmap
from PySide6.QtCore import Qt, Signal, QPointF


class CanvasView(QWidget):
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)

        self.pixmap = None
        self.image_path = None
        self.forge_report = None

        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self.dragging = False
        self.last_mouse = None

    def load_image(self, path):
        image = QImage(path)
        if image.isNull():
            return False

        self.pixmap = QPixmap.fromImage(image)
        self.image_path = path
        self.forge_report = None
        self.reset_view()
        self._emit_status()
        return True

    def set_forge_report(self, report):
        self.forge_report = report
        self.update()

    def clear_forge_report(self):
        self.forge_report = None
        self.update()

    def reset_view(self):
        if self.pixmap is None:
            self.zoom = 1.0
            self.pan = QPointF(0, 0)
            self.update()
            self.status_changed.emit("READY  |  INSERT IMAGE TO START")
            return

        margin = 80
        available_w = max(1, self.width() - margin)
        available_h = max(1, self.height() - margin)

        self.zoom = min(
            available_w / self.pixmap.width(),
            available_h / self.pixmap.height(),
            1.0
        )

        draw_w = self.pixmap.width() * self.zoom
        draw_h = self.pixmap.height() * self.zoom

        self.pan = QPointF(
            (self.width() - draw_w) / 2,
            (self.height() - draw_h) / 2
        )

        self.update()
        self._emit_status()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#05050c"))

        self._draw_grid(painter)

        border_pen = QPen(QColor("#00f5ff"))
        border_pen.setWidth(3)
        painter.setPen(border_pen)
        painter.drawRect(10, 10, self.width() - 20, self.height() - 20)

        if self.pixmap is None:
            self._draw_placeholder(painter)
        else:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
            target = self._image_target_rect()
            painter.drawPixmap(target, self.pixmap)
            self._draw_forge_overlay(painter)

    def _draw_grid(self, painter):
        pen = QPen(QColor("#151530"))
        pen.setWidth(1)
        painter.setPen(pen)

        grid = 40
        ox = int(self.pan.x()) % grid
        oy = int(self.pan.y()) % grid

        for x in range(ox, self.width(), grid):
            painter.drawLine(x, 0, x, self.height())
        for y in range(oy, self.height(), grid):
            painter.drawLine(0, y, self.width(), y)

    def _draw_placeholder(self, painter):
        painter.setFont(QFont("Consolas", 24, QFont.Bold))
        painter.setPen(QColor("#39ff14"))
        painter.drawText(self.rect(), Qt.AlignCenter, "INSERT IMAGE\n\nTO BEGIN")

    def _image_target_rect(self):
        from PySide6.QtCore import QRectF
        return QRectF(
            self.pan.x(),
            self.pan.y(),
            self.pixmap.width() * self.zoom,
            self.pixmap.height() * self.zoom
        )

    def _draw_forge_overlay(self, painter):
        if self.forge_report is None:
            return

        painter.save()

        red = QColor("#ff2b2b")
        red.setAlpha(220)

        pen = QPen(red)
        pen.setWidth(max(2, int(2 * self.zoom)))
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.setFont(QFont("Consolas", max(10, int(14 * self.zoom)), QFont.Bold))

        for index, problem in enumerate(self.forge_report.problems, start=1):
            if not problem.bbox:
                continue

            x, y, w, h = problem.bbox

            sx = self.pan.x() + x * self.zoom
            sy = self.pan.y() + y * self.zoom
            sw = w * self.zoom
            sh = h * self.zoom

            painter.drawRect(sx, sy, sw, sh)

            if problem.centroid:
                cx, cy = problem.centroid
                tx = self.pan.x() + cx * self.zoom
                ty = self.pan.y() + cy * self.zoom
                painter.drawText(tx, ty, str(index))

        painter.restore()

    def wheelEvent(self, event):
        if self.pixmap is None:
            return

        old_zoom = self.zoom
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.zoom = max(0.03, min(40.0, self.zoom * factor))

        mouse = event.position()
        image_x = (mouse.x() - self.pan.x()) / old_zoom
        image_y = (mouse.y() - self.pan.y()) / old_zoom

        self.pan = QPointF(
            mouse.x() - image_x * self.zoom,
            mouse.y() - image_y * self.zoom
        )

        self.update()
        self._emit_status()

    def mousePressEvent(self, event):
        if event.button() in (Qt.RightButton, Qt.MiddleButton):
            self.dragging = True
            self.last_mouse = event.position()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.dragging and self.last_mouse is not None:
            current = event.position()
            delta = current - self.last_mouse
            self.pan += delta
            self.last_mouse = current
            self.update()
            self._emit_status()
        else:
            self._emit_status(event.position())

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.RightButton, Qt.MiddleButton):
            self.dragging = False
            self.last_mouse = None
            self.setCursor(Qt.ArrowCursor)

    def _emit_status(self, mouse_pos=None):
        if self.pixmap is None:
            self.status_changed.emit("READY  |  INSERT IMAGE TO START  |  ZERO ISLANDS IS THE GOAL")
            return

        status = (
            f"IMAGE: {self.pixmap.width()} x {self.pixmap.height()} px"
            f"  |  ZOOM: {self.zoom * 100:.1f}%"
        )

        if mouse_pos is not None:
            ix = int((mouse_pos.x() - self.pan.x()) / self.zoom)
            iy = int((mouse_pos.y() - self.pan.y()) / self.zoom)
            if 0 <= ix < self.pixmap.width() and 0 <= iy < self.pixmap.height():
                status += f"  |  CURSOR: {ix}, {iy}"

        self.status_changed.emit(status)

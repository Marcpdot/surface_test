from __future__ import annotations

from matplotlib.figure import Figure
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from surface.blocks.base import Block
from surface.protocol import Command, PlotCommand

_PLOT_HEIGHT = 320


class PlotBlock(Block):
    def __init__(self, command_id: str, parent: QWidget | None = None) -> None:
        super().__init__(command_id, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(_PLOT_HEIGHT)

        # Imported here so backend_qtagg is not loaded at module import.
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._canvas)
        layout.addWidget(self._label)

    def command_type(self) -> str:
        return "plot"

    def render(self, command: Command) -> None:
        if not isinstance(command, PlotCommand):
            self._show_fallback("plot render failed: TypeError")
            return
        try:
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            for series in command.series:
                if series.kind == "line":
                    ax.plot(series.x, series.y, label=series.label or None)
                elif series.kind == "scatter":
                    ax.scatter(series.x, series.y, label=series.label or None)
                else:
                    ax.bar(series.x, series.y, label=series.label or None)
            if command.title:
                ax.set_title(command.title)
            if command.xlabel:
                ax.set_xlabel(command.xlabel)
            if command.ylabel:
                ax.set_ylabel(command.ylabel)
            if any(s.label for s in command.series):
                ax.legend()
            self._canvas.draw()
            self._canvas.show()
            self._label.hide()
        except Exception as exc:
            self._show_fallback(f"plot render failed: {type(exc).__name__}")

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), _PLOT_HEIGHT)

    def _show_fallback(self, message: str) -> None:
        try:
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
            ax.set_axis_off()
            self._canvas.draw()
            self._canvas.show()
            self._label.hide()
        except Exception:
            self._label.setText(message)
            self._label.show()
            self._canvas.hide()

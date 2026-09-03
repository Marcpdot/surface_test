from __future__ import annotations

from PySide6.QtWidgets import QWidget

from surface.protocol import Command


class Block(QWidget):
    def __init__(self, command_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._command_id = command_id

    @property
    def command_id(self) -> str:
        return self._command_id

    def command_type(self) -> str:
        raise NotImplementedError

    def render(self, command: Command) -> None:
        """Oppdater widget fra command. Kalles ved create og upsert.

        Hard regel: kaster aldri. Fang ProtocolError, mathtext- og
        matplotlib-feil; vis fallback-tekst i widgeten og returner.
        """
        raise NotImplementedError

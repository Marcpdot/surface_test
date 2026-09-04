from PySide6.QtWidgets import QWidget

from surface.blocks.base import Block
from surface.blocks.equation import EquationBlock
from surface.blocks.image import ImageBlock
from surface.blocks.layout import LayoutBlock
from surface.blocks.plot import PlotBlock
from surface.blocks.text import TextBlock
from surface.dispatcher import UnknownBlockError
from surface.protocol import Command

_FACTORIES = {
    "text": TextBlock,
    "equation": EquationBlock,
    "image": ImageBlock,
    "plot": PlotBlock,
    "layout": LayoutBlock,
}


def create_block(command: Command, parent: QWidget | None = None) -> Block:
    """Factory. Mapper command.type → konkret Block-subklasse.

    Raises:
        UnknownBlockError: type ikke i _FACTORIES.
    """
    factory = _FACTORIES.get(command.type)
    if factory is None:
        raise UnknownBlockError(command.id, command.type)
    return factory(command.id, parent)

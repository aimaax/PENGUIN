from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Signal, Qt

class DoubleSlider(QSlider):
    doubleValueChanged = Signal(float)

    def __init__(self, orientation=Qt.Horizontal, decimals=3, *args, **kwargs):
        super().__init__(orientation, *args, **kwargs)
        self._multi = 10 ** decimals
        self._step = None  # will store the float step
        self.valueChanged.connect(self._emit_double_value_changed)

    def _emit_double_value_changed(self):
        value = float(super().value()) / self._multi
        # Snap to step if defined
        if self._step is not None:
            value = round(value / self._step) * self._step
            super().setValue(int(value * self._multi))
        self.doubleValueChanged.emit(value)

    def value(self):
        return float(super().value()) / self._multi

    def setMinimum(self, value):
        super().setMinimum(int(value * self._multi))

    def setMaximum(self, value):
        super().setMaximum(int(value * self._multi))

    def setSingleStep(self, value):
        """Sets both internal integer step and snap step in float."""
        self._step = value
        super().setSingleStep(int(value * self._multi))

    def singleStep(self):
        return self._step

    def setValue(self, value):
        super().setValue(int(value * self._multi))

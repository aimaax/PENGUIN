from PySide6.QtWidgets import QComboBox, QListWidget, QListWidgetItem, QCheckBox, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._external_callbacks = []
        self._suppress_callbacks = False  # Flag to suppress callbacks during batch operations
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.setPlaceholderText("Select campaigns...")
        self.lineEdit().setAlignment(Qt.AlignLeft)
        self.lineEdit().setCursorPosition(0)
        
        self.list_widget = QListWidget(self)
        self.setModel(self.list_widget.model())
        self.setView(self.list_widget)
        
    def add_external_callback(self, callback):
        """Register a new external callback to be run when selection changes."""
        if callable(callback):
            self._external_callbacks.append(callback)
            
    def _trigger_external_callbacks(self):
        """Trigger all external callbacks only if not suppressed."""
        if not self._suppress_callbacks:
            for callback in self._external_callbacks:
                callback()
        
    def addItems(self, items, select_all=False):
        """Add items to the combo box with checkboxes."""
        for item in items:
            self.addItem(item, checked=select_all)
        if select_all == True:
            self.update_selected_items()

    def addItem(self, text, checked=False, show_fitted_checkbox=False, fitted=False, show_sensor_info_text=False, sensor_info_text: list[str] = None):
        """Add a single item with main checkbox (left) and optional fitted checkbox (right)."""
        item = QListWidgetItem(self.list_widget)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        checkbox = QCheckBox(text)
        checkbox.setChecked(checked)
        checkbox.stateChanged.connect(self.update_selected_items)
        checkbox.stateChanged.connect(lambda _: self._trigger_external_callbacks())
        layout.addWidget(checkbox)

        if show_fitted_checkbox:
            fitted_label = QLabel("✅" if fitted else "❌")
            layout.addWidget(fitted_label, alignment=Qt.AlignRight)
            
        if show_sensor_info_text:
            sensor_info_text = QLabel(" | ".join(sensor_info_text))
            layout.addWidget(sensor_info_text, alignment=Qt.AlignRight)

        widget.setLayout(layout)
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        self.update_selected_items()
    
    def update_selected_items(self):
        """Update the combo box text to show selected items."""
        selected_items = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            if widget:  
                checkboxes = widget.findChildren(QCheckBox)
                if checkboxes and checkboxes[0].isChecked():
                    selected_items.append(checkboxes[0].text())
        self.lineEdit().setText(", ".join(selected_items))
        
    def get_selected_items(self):
        """Return a list of selected items."""
        selected_items = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            if widget:
                checkboxes = widget.findChildren(QCheckBox)
                if checkboxes and checkboxes[0].isChecked():
                    selected_items.append(checkboxes[0].text())
        return selected_items
    
    def select_first_index(self):
        """Select the first item in the combo box."""
        if self.list_widget.count() > 0:
            first_item = self.list_widget.item(0)
            widget = self.list_widget.itemWidget(first_item)
            checkbox = widget.findChildren(QCheckBox)[0]
            checkbox.setChecked(True)
            self.update_selected_items()
    
    def select_from_list(self, items):
        """Select items from a list. Suppresses callbacks as this is programmatic."""
        self._suppress_callbacks = True  # Suppress callbacks during programmatic selection
        for item in items:
            for index in range(self.list_widget.count()):
                widget = self.list_widget.itemWidget(self.list_widget.item(index))
                checkbox = widget.findChildren(QCheckBox)[0]
                if checkbox.text() == item:
                    checkbox.setChecked(True)
        self.update_selected_items()
        self._suppress_callbacks = False  # Re-enable callbacks
        # Do NOT trigger callbacks here - this is programmatic restoration, not user action
                    
    def select_all(self):
        """Select all items in the combo box. Triggers callbacks once after all selections."""
        self._suppress_callbacks = True  # Suppress callbacks during batch operation
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            checkbox = widget.findChildren(QCheckBox)[0]
            checkbox.setChecked(True)
        self.update_selected_items()
        self._suppress_callbacks = False  # Re-enable callbacks
        self._trigger_external_callbacks()  # Trigger once after all selections
        
    def deselect_all(self):
        """Deselect all items in the combo box. Triggers callbacks once after all deselections."""
        self._suppress_callbacks = True  # Suppress callbacks during batch operation
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            checkbox = widget.findChildren(QCheckBox)[0]
            checkbox.setChecked(False)
        self.update_selected_items()
        self._suppress_callbacks = False  # Re-enable callbacks
        self._trigger_external_callbacks()  # Trigger once after all deselections
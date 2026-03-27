"""Dashboard panel — device status cards + RTT graph + summary."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
import pyqtgraph as pg

from desktop.theme import Colors, Fonts

STATUS_COLORS = {
    "connected": Colors.CONNECTED,
    "disconnected": Colors.DISCONNECTED,
    "delayed": Colors.DELAYED,
    "unknown": Colors.TEXT_MUTED,
}

STATUS_BG = {
    "connected": Colors.CONNECTED_DIM,
    "disconnected": Colors.DISCONNECTED_DIM,
    "delayed": Colors.DELAYED_DIM,
    "unknown": "#2a2a4a",
}


class DeviceCard(QFrame):
    """Single device status card."""

    clicked = Signal(str)  # device_id

    def __init__(self, device_data, parent=None):
        super().__init__(parent)
        self._device_id = device_data.get('id', '')
        self._status = "unknown"
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui(device_data)
        self._apply_style()

    def _build_ui(self, data):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Status dot
        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)
        layout.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self._name_label = QLabel(data.get('name', ''))
        self._name_label.setStyleSheet(f"font-size: {Fonts.SIZE_MD}px; font-weight: 500; color: {Colors.TEXT}; background: transparent;")
        info_layout.addWidget(self._name_label)

        self._ip_label = QLabel(data.get('ip', ''))
        self._ip_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_DIM}; font-family: '{Fonts.MONO}'; background: transparent;")
        info_layout.addWidget(self._ip_label)

        cat = data.get('category', '')
        self._cat_label = QLabel(cat)
        self._cat_label.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;")
        info_layout.addWidget(self._cat_label)

        layout.addLayout(info_layout, 1)

        # RTT
        rtt_layout = QVBoxLayout()
        rtt_layout.setSpacing(0)
        rtt_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._rtt_label = QLabel("--")
        self._rtt_label.setStyleSheet(f"font-size: {Fonts.SIZE_LG}px; font-weight: 600; color: {Colors.TEXT}; font-family: '{Fonts.MONO}'; background: transparent;")
        self._rtt_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        rtt_layout.addWidget(self._rtt_label)

        self._rtt_unit = QLabel("ms")
        self._rtt_unit.setStyleSheet(f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;")
        self._rtt_unit.setAlignment(Qt.AlignmentFlag.AlignRight)
        rtt_layout.addWidget(self._rtt_unit)

        layout.addLayout(rtt_layout)

    def _apply_style(self):
        color = STATUS_COLORS.get(self._status, Colors.TEXT_MUTED)
        bg = STATUS_BG.get(self._status, "#2a2a4a")
        self.setStyleSheet(f"""
            DeviceCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
            DeviceCard:hover {{
                border-color: {color};
            }}
        """)
        self._dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

    def update_status(self, status, rtt_ms):
        self._status = status
        color = STATUS_COLORS.get(status, Colors.TEXT_MUTED)

        if rtt_ms is not None:
            self._rtt_label.setText(f"{rtt_ms:,}")
            self._rtt_label.setStyleSheet(
                f"font-size: {Fonts.SIZE_LG}px; font-weight: 600; color: {color}; "
                f"font-family: '{Fonts.MONO}'; background: transparent;"
            )
        else:
            self._rtt_label.setText("--")
            self._rtt_label.setStyleSheet(
                f"font-size: {Fonts.SIZE_LG}px; font-weight: 600; color: {Colors.TEXT_MUTED}; "
                f"font-family: '{Fonts.MONO}'; background: transparent;"
            )

        self._dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        self._apply_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self._device_id)
        super().mousePressEvent(event)


class SummaryBar(QWidget):
    """Summary bar showing connected/disconnected/delayed counts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._labels = {}
        for key, label_text, color in [
            ("total", "Total", Colors.TEXT),
            ("connected", "Connected", Colors.CONNECTED),
            ("disconnected", "Disconnected", Colors.DISCONNECTED),
            ("delayed", "Delayed", Colors.DELAYED),
        ]:
            item = QHBoxLayout()
            item.setSpacing(4)

            count = QLabel("0")
            count.setStyleSheet(
                f"font-size: {Fonts.SIZE_LG}px; font-weight: 600; color: {color}; "
                f"font-family: '{Fonts.MONO}'; background: transparent;"
            )
            item.addWidget(count)

            name = QLabel(label_text)
            name.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
            item.addWidget(name)

            layout.addLayout(item)
            self._labels[key] = count

        layout.addStretch()

    def update_counts(self, total, connected, disconnected, delayed):
        self._labels["total"].setText(f"{total}")
        self._labels["connected"].setText(f"{connected}")
        self._labels["disconnected"].setText(f"{disconnected}")
        self._labels["delayed"].setText(f"{delayed}")


class DashboardPanel(QWidget):
    """Main dashboard with device cards, summary, and RTT graph."""

    device_selected = Signal(str)
    add_device_requested = Signal()
    edit_device_requested = Signal(str)
    delete_device_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = {}  # device_id -> DeviceCard
        self._selected_device = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_XL}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ Add Device")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self.add_device_requested.emit)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Summary
        self._summary = SummaryBar()
        layout.addWidget(self._summary)

        # Splitter: cards (left) + graph (right)
        content = QHBoxLayout()
        content.setSpacing(12)

        # Device cards scroll area
        card_scroll = QScrollArea()
        card_scroll.setWidgetResizable(True)
        card_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        card_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        card_scroll.setMinimumWidth(260)
        card_scroll.setMaximumWidth(360)

        self._card_container = QWidget()
        self._card_container.setStyleSheet("background: transparent;")
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(0, 0, 4, 0)
        self._card_layout.setSpacing(6)
        self._card_layout.addStretch()
        card_scroll.setWidget(self._card_container)

        content.addWidget(card_scroll)

        # RTT Graph
        graph_container = QVBoxLayout()
        graph_container.setSpacing(4)

        graph_header = QHBoxLayout()
        self._graph_title = QLabel("RTT History")
        self._graph_title.setStyleSheet(f"font-size: {Fonts.SIZE_MD}px; font-weight: 500; color: {Colors.TEXT_DIM}; background: transparent;")
        graph_header.addWidget(self._graph_title)
        graph_header.addStretch()
        graph_container.addLayout(graph_header)

        self._graph = pg.PlotWidget()
        self._graph.setBackground(Colors.BG_CARD)
        self._graph.showGrid(x=True, y=True, alpha=0.1)
        self._graph.setLabel('left', 'RTT', units='ms')
        self._graph.setLabel('bottom', 'Sample')
        self._graph.getAxis('left').setPen(pg.mkPen(Colors.TEXT_MUTED))
        self._graph.getAxis('bottom').setPen(pg.mkPen(Colors.TEXT_MUTED))
        self._graph.getAxis('left').setTextPen(pg.mkPen(Colors.TEXT_DIM))
        self._graph.getAxis('bottom').setTextPen(pg.mkPen(Colors.TEXT_DIM))
        self._graph.setMinimumHeight(200)

        self._graph_curves = {}

        graph_container.addWidget(self._graph, 1)

        content.addLayout(graph_container, 1)
        layout.addLayout(content, 1)

    def set_devices(self, devices):
        """Initialize device cards from device list."""
        # Clear existing
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # Remove stretch
        while self._card_layout.count() > 0:
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for dev in devices:
            card = DeviceCard(dev.to_dict() if hasattr(dev, 'to_dict') else dev)
            card.clicked.connect(self._on_card_clicked)
            self._card_layout.addWidget(card)
            dev_id = dev.id if hasattr(dev, 'id') else dev.get('id', '')
            self._cards[dev_id] = card

        self._card_layout.addStretch()

    def update_ping_data(self, results):
        """Update device cards with ping results."""
        counts = {"connected": 0, "disconnected": 0, "delayed": 0}

        for r in results:
            dev_id = r.get('device_id', '')
            status = r.get('status', 'unknown')
            rtt = r.get('rtt_ms')

            if dev_id in self._cards:
                self._cards[dev_id].update_status(status, rtt)

            if status in counts:
                counts[status] += 1

        total = len(results)
        self._summary.update_counts(total, counts["connected"], counts["disconnected"], counts["delayed"])

    def update_rtt_graph(self, rtt_history):
        """Update RTT graph with history data."""
        # Clear old curves
        self._graph.clear()
        self._graph_curves.clear()

        colors = [Colors.ACCENT, Colors.CONNECTED, Colors.WARNING, Colors.DISCONNECTED,
                  "#bb86fc", "#03dac6", "#ff7597", "#ffa726"]

        for i, (dev_id, history) in enumerate(rtt_history.items()):
            if not history:
                continue
            y_data = [h.get('rtt_ms') or 0 for h in history]
            x_data = list(range(len(y_data)))
            color = colors[i % len(colors)]
            pen = pg.mkPen(color=color, width=2)
            curve = self._graph.plot(x_data, y_data, pen=pen, name=dev_id)
            self._graph_curves[dev_id] = curve

    def _on_card_clicked(self, device_id):
        self._selected_device = device_id
        self.device_selected.emit(device_id)

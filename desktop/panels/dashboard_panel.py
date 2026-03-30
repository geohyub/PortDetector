"""Dashboard panel — device status cards + monitoring overview + focused RTT graph."""

from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
import pyqtgraph as pg

from desktop.theme import Colors, Fonts
from desktop.i18n import t
from backend.utils.monitoring_presenter import (
    severity_label,
    severity_rank,
)


STATUS_COLORS = {
    "connected": Colors.CONNECTED,
    "disconnected": Colors.DISCONNECTED,
    "delayed": Colors.DELAYED,
    "unknown": Colors.TEXT_MUTED,
}

SEVERITY_COLORS = {
    "stable": Colors.CONNECTED,
    "info": Colors.ACCENT,
    "advisory": Colors.WARNING,
    "warning": Colors.WARNING,
    "critical": Colors.DISCONNECTED,
    "emergency": Colors.DISCONNECTED,
}


class DeviceCard(QFrame):
    """Single device status card."""

    clicked = Signal(str)

    def __init__(self, device_data, parent=None):
        super().__init__(parent)
        self._device_id = device_data.get('id', '')
        self._status = "unknown"
        self._severity = "info"
        self._selected = False
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui(device_data)
        self._apply_style()

    def _build_ui(self, data):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)
        layout.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignTop)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._name_label = QLabel(data.get('name', ''))
        self._name_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_MD}px; font-weight: 600; color: {Colors.TEXT}; background: transparent;"
        )
        top_row.addWidget(self._name_label)

        self._importance_label = QLabel("Standard")
        self._importance_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;"
        )
        top_row.addWidget(self._importance_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addStretch()
        info_layout.addLayout(top_row)

        self._status_label = QLabel("Waiting for data")
        self._status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; font-weight: 500; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        info_layout.addWidget(self._status_label)

        self._meta_label = QLabel(data.get('ip', ''))
        self._meta_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        info_layout.addWidget(self._meta_label)

        self._detail_label = QLabel("")
        self._detail_label.setWordWrap(True)
        self._detail_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;"
        )
        info_layout.addWidget(self._detail_label)

        layout.addLayout(info_layout, 1)

        rtt_layout = QVBoxLayout()
        rtt_layout.setSpacing(0)
        rtt_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        self._rtt_label = QLabel("--")
        self._rtt_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {Colors.TEXT}; "
            f"font-family: '{Fonts.FAMILY}'; background: transparent;"
        )
        self._rtt_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        rtt_layout.addWidget(self._rtt_label)

        self._rtt_unit = QLabel("ms")
        self._rtt_unit.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;"
        )
        self._rtt_unit.setAlignment(Qt.AlignmentFlag.AlignRight)
        rtt_layout.addWidget(self._rtt_unit)

        layout.addLayout(rtt_layout)

    def _apply_style(self):
        color = STATUS_COLORS.get(self._status, Colors.TEXT_MUTED)
        severity_color = SEVERITY_COLORS.get(self._severity, color)
        selected_border = severity_color if self._selected else Colors.BORDER

        self.setStyleSheet(
            f"""
            DeviceCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {selected_border};
                border-radius: 8px;
            }}
            DeviceCard:hover {{
                border-color: {severity_color};
            }}
        """
        )
        self._dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style()

    def update_snapshot(self, snapshot: dict):
        self._status = snapshot.get('status', 'unknown')
        self._severity = snapshot.get('severity', 'info')

        color = STATUS_COLORS.get(self._status, Colors.TEXT_MUTED)
        severity_color = SEVERITY_COLORS.get(self._severity, color)

        self._status_label.setText(snapshot.get('status_label', 'Waiting for data'))
        self._status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; font-weight: 600; color: {severity_color}; background: transparent;"
        )

        meta_parts = [snapshot.get('ip', ''), snapshot.get('category', '')]
        self._meta_label.setText(" | ".join(part for part in meta_parts if part))
        self._detail_label.setText(snapshot.get('last_change_text', ''))
        self._importance_label.setText(snapshot.get('importance_label', 'Standard'))

        rtt_ms = snapshot.get('rtt_ms')
        if rtt_ms is not None:
            self._rtt_label.setText(f"{rtt_ms:,}")
            self._rtt_label.setStyleSheet(
                f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {severity_color}; "
                f"font-family: '{Fonts.FAMILY}'; background: transparent;"
            )
        else:
            self._rtt_label.setText("--")
            self._rtt_label.setStyleSheet(
                f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {Colors.TEXT_MUTED}; "
                f"font-family: '{Fonts.FAMILY}'; background: transparent;"
            )

        self._apply_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self._device_id)
        super().mousePressEvent(event)


class SummaryBar(QWidget):
    """Compact summary counts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self._labels = {}
        self._name_labels = {}
        for key, i18n_key, color in [
            ("total", "dash.monitored", Colors.TEXT),
            ("stable", "dash.stable", Colors.CONNECTED),
            ("attention", "dash.attention", Colors.WARNING),
            ("offline", "dash.offline", Colors.DISCONNECTED),
        ]:
            label_text = t(i18n_key)
            item = QHBoxLayout()
            item.setSpacing(5)

            count = QLabel("0")
            count.setStyleSheet(
                f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {color}; "
                f"font-family: '{Fonts.FAMILY}'; background: transparent;"
            )
            item.addWidget(count)

            name = QLabel(label_text)
            name.setStyleSheet(
                f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
            )
            item.addWidget(name)

            layout.addLayout(item)
            self._labels[key] = count
            self._name_labels[key] = (name, i18n_key)

        layout.addStretch()

    def retranslate(self):
        for key, (label, i18n_key) in self._name_labels.items():
            label.setText(t(i18n_key))

    def update_counts(self, total, stable, attention, offline):
        self._labels["total"].setText(f"{total}")
        self._labels["stable"].setText(f"{stable}")
        self._labels["attention"].setText(f"{attention}")
        self._labels["offline"].setText(f"{offline}")


class OverviewBanner(QFrame):
    """High-level monitoring summary."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            OverviewBanner {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self._headline = QLabel(t("dash.waiting_sweep"))
        self._headline.setStyleSheet(
            f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        layout.addWidget(self._headline)

        self._detail = QLabel(t("dash.waiting_detail"))
        self._detail.setWordWrap(True)
        self._detail.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        layout.addWidget(self._detail)

        self._context = QLabel("")
        self._context.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;"
        )
        layout.addWidget(self._context)

    def update_data(self, overview: dict):
        severity = overview.get('severity', 'info')
        color = SEVERITY_COLORS.get(severity, Colors.ACCENT)
        self.setStyleSheet(
            f"""
            OverviewBanner {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {color};
                border-radius: 8px;
            }}
        """
        )
        self._headline.setText(overview.get('headline', 'Waiting for first monitoring sweep'))
        self._headline.setStyleSheet(
            f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {color}; background: transparent;"
        )
        self._detail.setText(overview.get('detail', ''))
        self._context.setText(overview.get('context', ''))


class DeviceDetailPanel(QFrame):
    """Focused explanation for the selected device."""

    scan_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._device_id = ""
        self.setStyleSheet(
            f"""
            DeviceDetailPanel {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self._title = QLabel(t("dash.selected_device"))
        self._title.setStyleSheet(
            f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        top_row.addWidget(self._title)

        top_row.addStretch()

        self._severity = QLabel("Info")
        self._severity.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;"
        )
        top_row.addWidget(self._severity)
        layout.addLayout(top_row)

        self._status = QLabel(t("dash.select_prompt"))
        self._status.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; font-weight: 600; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        layout.addWidget(self._status)

        self._reason = QLabel("")
        self._reason.setWordWrap(True)
        self._reason.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        layout.addWidget(self._reason)

        self._meta = QLabel("")
        self._meta.setWordWrap(True)
        self._meta.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;"
        )
        layout.addWidget(self._meta)

        self._ports = QLabel("")
        self._ports.setWordWrap(True)
        self._ports.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        layout.addWidget(self._ports)

        self._action = QLabel("")
        self._action.setWordWrap(True)
        self._action.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT}; background: transparent;"
        )
        layout.addWidget(self._action)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._scan_btn = QPushButton(t("dash.open_scanner"))
        self._scan_btn.setObjectName("btn_primary")
        self._scan_btn.setFixedHeight(30)
        self._scan_btn.setEnabled(False)
        self._scan_btn.clicked.connect(self._emit_scan_requested)
        btn_row.addWidget(self._scan_btn)
        layout.addLayout(btn_row)

    def update_detail(self, detail: dict):
        if not detail:
            self._device_id = ""
            self._title.setText("Selected device")
            self._severity.setText("Info")
            self._status.setText("Select a device card to inspect it.")
            self._reason.setText("")
            self._meta.setText("")
            self._ports.setText("")
            self._action.setText("")
            self._scan_btn.setEnabled(False)
            return

        self._device_id = detail.get('device_id', '')
        severity = detail.get('severity', 'info')
        color = SEVERITY_COLORS.get(severity, Colors.ACCENT)

        self.setStyleSheet(
            f"""
            DeviceDetailPanel {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {color};
                border-radius: 8px;
            }}
        """
        )

        self._title.setText(detail.get('name', 'Selected device'))
        self._severity.setText(severity_label(severity))
        self._severity.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; font-weight: 700; color: {color}; background: transparent;"
        )
        self._status.setText(detail.get('status_label', 'Waiting for data'))
        self._status.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; font-weight: 700; color: {color}; background: transparent;"
        )
        self._reason.setText(detail.get('reason', ''))
        self._meta.setText(detail.get('meta_text', ''))
        self._ports.setText(detail.get('ports_text', ''))
        self._action.setText(detail.get('action_text', ''))
        self._scan_btn.setEnabled(bool(detail.get('has_ports')))

    def _emit_scan_requested(self):
        if self._device_id:
            self.scan_requested.emit(self._device_id)


class DashboardPanel(QWidget):
    """Main dashboard with device cards, overview, and focused RTT graph."""

    device_selected = Signal(str)
    add_device_requested = Signal()
    scan_device_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = {}
        self._selected_device = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        header = QHBoxLayout()
        self._title = QLabel(t("dash.title"))
        self._title.setStyleSheet(
            f"font-size: {Fonts.SIZE_XL}px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        header.addWidget(self._title)
        header.addStretch()

        self._add_btn = QPushButton(t("dash.add_device"))
        self._add_btn.setObjectName("btn_primary")
        self._add_btn.setFixedHeight(32)
        self._add_btn.clicked.connect(self.add_device_requested.emit)
        header.addWidget(self._add_btn)
        layout.addLayout(header)

        self._guide_label = QLabel(t("guide.dashboard"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        self._summary = SummaryBar()
        layout.addWidget(self._summary)

        self._overview = OverviewBanner()
        layout.addWidget(self._overview)

        content = QHBoxLayout()
        content.setSpacing(12)

        card_scroll = QScrollArea()
        card_scroll.setWidgetResizable(True)
        card_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        card_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        card_scroll.setMinimumWidth(290)
        card_scroll.setMaximumWidth(380)

        self._card_container = QWidget()
        self._card_container.setStyleSheet("background: transparent;")
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(0, 0, 4, 0)
        self._card_layout.setSpacing(8)
        self._card_layout.addStretch()
        card_scroll.setWidget(self._card_container)
        content.addWidget(card_scroll)

        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        self._detail = DeviceDetailPanel()
        self._detail.scan_requested.connect(self.scan_device_requested.emit)
        right_col.addWidget(self._detail)

        graph_container = QFrame()
        graph_container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """
        )
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(12, 10, 12, 12)
        graph_layout.setSpacing(6)

        self._graph_title = QLabel(t("dash.rtt_trend"))
        self._graph_title.setStyleSheet(
            f"font-size: {Fonts.SIZE_MD}px; font-weight: 600; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        graph_layout.addWidget(self._graph_title)

        self._graph_subtitle = QLabel(t("dash.rtt_subtitle"))
        self._graph_subtitle.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent;"
        )
        graph_layout.addWidget(self._graph_subtitle)

        self._graph = pg.PlotWidget()
        self._graph.setBackground(Colors.BG_CARD)
        self._graph.showGrid(x=True, y=True, alpha=0.12)
        self._graph.setLabel('left', 'RTT', units='ms')
        self._graph.setLabel('bottom', 'Sample')
        self._graph.getAxis('left').setPen(pg.mkPen(Colors.TEXT_MUTED))
        self._graph.getAxis('bottom').setPen(pg.mkPen(Colors.TEXT_MUTED))
        self._graph.getAxis('left').setTextPen(pg.mkPen(Colors.TEXT_DIM))
        self._graph.getAxis('bottom').setTextPen(pg.mkPen(Colors.TEXT_DIM))
        self._graph.setMinimumHeight(260)
        graph_layout.addWidget(self._graph, 1)

        right_col.addWidget(graph_container, 1)
        content.addLayout(right_col, 1)
        layout.addLayout(content, 1)

    def set_devices(self, devices):
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        while self._card_layout.count() > 0:
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for dev in devices:
            payload = dev.to_dict() if hasattr(dev, 'to_dict') else dev
            card = DeviceCard(payload)
            card.clicked.connect(self._on_card_clicked)
            dev_id = payload.get('id', '')
            self._cards[dev_id] = card

        self._card_layout.addStretch()

    def set_selected_device(self, device_id: str | None):
        self._selected_device = device_id
        for dev_id, card in self._cards.items():
            card.set_selected(dev_id == device_id)

    def update_device_snapshots(self, snapshots: list[dict]):
        while self._card_layout.count() > 0:
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        stable = 0
        attention = 0
        offline = 0

        for snapshot in snapshots:
            dev_id = snapshot.get('device_id', '')
            card = self._cards.get(dev_id)
            if not card:
                card = DeviceCard(snapshot)
                card.clicked.connect(self._on_card_clicked)
                self._cards[dev_id] = card

            card.update_snapshot(snapshot)
            card.set_selected(dev_id == self._selected_device)
            self._card_layout.addWidget(card)

            if snapshot.get('status') == "connected":
                stable += 1
            else:
                attention += 1
                if snapshot.get('status') == "disconnected":
                    offline += 1

        self._card_layout.addStretch()
        self._summary.update_counts(len(snapshots), stable, attention, offline)

    def update_overview(self, overview: dict):
        self._overview.update_data(overview)

    def update_device_detail(self, detail: dict):
        self._detail.update_detail(detail)

    def update_rtt_graph(
        self,
        rtt_history: dict,
        selected_device_id: str | None = None,
        selected_device_name: str | None = None,
        delay_threshold_ms: int | None = None,
    ):
        self._graph.clear()

        focus_id = selected_device_id if selected_device_id in rtt_history else None
        if not focus_id:
            for dev_id, history in rtt_history.items():
                if history:
                    focus_id = dev_id
                    break

        if not focus_id:
            self._graph_title.setText(t("dash.rtt_trend"))
            self._graph_subtitle.setText(t("dash.no_samples"))
            return

        history = rtt_history.get(focus_id, [])
        label = selected_device_name or focus_id
        self._graph_title.setText(f"{t('dash.rtt_trend')} - {label}")
        self._graph_subtitle.setText(t("dash.rtt_subtitle"))

        x_data = list(range(len(history)))
        y_data = [
            float(sample.get('rtt_ms')) if sample.get('rtt_ms') is not None else float('nan')
            for sample in history
        ]
        pen = pg.mkPen(color=Colors.ACCENT, width=2)
        self._graph.plot(x_data, y_data, pen=pen, connect="finite")

        if delay_threshold_ms:
            threshold_pen = pg.mkPen(color=Colors.WARNING, width=1, style=Qt.PenStyle.DashLine)
            self._graph.addItem(pg.InfiniteLine(pos=delay_threshold_ms, angle=0, pen=threshold_pen))

    def retranslate(self):
        self._title.setText(t("dash.title"))
        self._guide_label.setText(t("guide.dashboard"))
        self._add_btn.setText(t("dash.add_device"))
        self._summary.retranslate()
        self._graph_title.setText(t("dash.rtt_trend"))
        self._graph_subtitle.setText(t("dash.rtt_subtitle"))
        self._detail._scan_btn.setText(t("dash.open_scanner"))

    def _on_card_clicked(self, device_id):
        self.set_selected_device(device_id)
        self.device_selected.emit(device_id)

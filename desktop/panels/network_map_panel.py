"""Network Map panel — LAN topology visualization with QGraphicsScene."""

from __future__ import annotations

import csv
import math
import os
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QGraphicsScene, QGraphicsView,
    QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem,
    QFileDialog, QInputDialog, QComboBox, QFrame,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QBrush, QPen, QColor, QFont, QPainter, QImage,
)

from desktop.theme import Colors, Fonts
from desktop.i18n import t
from backend.services.discovery_service import get_local_subnet
from backend.services.network_map_service import MapNode, NetworkMapService


# ── Device type icons (simple colored shapes) ──

DEVICE_TYPE_COLORS = {
    "router": "#ff6b35",    # orange
    "switch": "#ffd166",    # yellow
    "server": "#00b4d8",    # accent blue
    "workstation": "#8888aa",  # gray
    "marine": "#06d6a0",    # green (connected color)
    "unknown": "#6a6a8a",   # muted
}

NODE_RADIUS = 22
LABEL_OFFSET_Y = 28


class NetworkNode(QGraphicsEllipseItem):
    """Draggable node in the topology graph."""

    def __init__(self, node_data: dict, parent=None):
        super().__init__(-NODE_RADIUS, -NODE_RADIUS, NODE_RADIUS * 2, NODE_RADIUS * 2, parent)
        self.data = node_data
        self._online = node_data.get('online', True)
        self._device_type = node_data.get('device_type', 'unknown')

        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

        # Styling
        self._apply_style()

        # IP label below
        self._ip_label = QGraphicsTextItem(self)
        ip_text = node_data.get('user_label') or node_data.get('ip', '')
        self._ip_label.setPlainText(ip_text)
        self._ip_label.setDefaultTextColor(QColor(Colors.TEXT_DIM))
        font = QFont(Fonts.FAMILY, Fonts.SIZE_XS - 2)
        self._ip_label.setFont(font)
        br = self._ip_label.boundingRect()
        self._ip_label.setPos(-br.width() / 2, LABEL_OFFSET_Y - 4)

        # Type abbreviation inside circle
        self._type_label = QGraphicsTextItem(self)
        abbrev = self._get_type_abbrev()
        self._type_label.setPlainText(abbrev)
        self._type_label.setDefaultTextColor(QColor("#ffffff"))
        type_font = QFont(Fonts.FAMILY, Fonts.SIZE_XS - 1)
        type_font.setWeight(QFont.Weight.Bold)
        self._type_label.setFont(type_font)
        tbr = self._type_label.boundingRect()
        self._type_label.setPos(-tbr.width() / 2, -tbr.height() / 2)

    def _get_type_abbrev(self) -> str:
        mapping = {
            "router": "R",
            "switch": "SW",
            "server": "S",
            "workstation": "PC",
            "marine": "M",
            "unknown": "?",
        }
        return mapping.get(self._device_type, "?")

    def _apply_style(self):
        base_color = DEVICE_TYPE_COLORS.get(self._device_type, Colors.TEXT_MUTED)
        if not self._online:
            base_color = Colors.DISCONNECTED

        self.setBrush(QBrush(QColor(base_color)))
        pen = QPen(QColor(Colors.BORDER_LIGHT), 2)
        if self.isSelected():
            pen = QPen(QColor(Colors.ACCENT), 3)
        self.setPen(pen)

    def set_online(self, online: bool):
        self._online = online
        self.data['online'] = online
        self._apply_style()

    def set_label(self, label: str):
        self.data['user_label'] = label
        display = label or self.data.get('ip', '')
        self._ip_label.setPlainText(display)
        br = self._ip_label.boundingRect()
        self._ip_label.setPos(-br.width() / 2, LABEL_OFFSET_Y - 4)

    def update_rtt(self, rtt_ms: Optional[int]):
        self.data['rtt_ms'] = rtt_ms

    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor(Colors.ACCENT), 3))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._apply_style()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            self.data['x'] = value.x()
            self.data['y'] = value.y()
        return super().itemChange(change, value)


class TopologyView(QGraphicsView):
    """Custom graphics view with zoom and pan."""

    node_clicked = Signal(dict)
    node_double_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet(
            f"QGraphicsView {{ background-color: {Colors.BG}; border: 1px solid {Colors.BORDER}; border-radius: 4px; }}"
        )
        self._zoom_level = 1.0
        self._nodes: Dict[str, NetworkNode] = {}
        self._edges: List[QGraphicsLineItem] = []
        self._gateway_ip = None

    def wheelEvent(self, event):
        factor = 1.15
        if event.angleDelta().y() > 0:
            self._zoom_level *= factor
            self.scale(factor, factor)
        else:
            self._zoom_level /= factor
            self.scale(1 / factor, 1 / factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, NetworkNode):
            self.node_clicked.emit(item.data)
        elif isinstance(item, QGraphicsTextItem) and isinstance(item.parentItem(), NetworkNode):
            self.node_clicked.emit(item.parentItem().data)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, NetworkNode):
            self.node_double_clicked.emit(item.data)
        elif isinstance(item, QGraphicsTextItem) and isinstance(item.parentItem(), NetworkNode):
            self.node_double_clicked.emit(item.parentItem().data)
        super().mouseDoubleClickEvent(event)

    def clear_all(self):
        self._scene.clear()
        self._nodes.clear()
        self._edges.clear()
        self._gateway_ip = None

    def add_node(self, node_data: dict) -> NetworkNode:
        gfx_node = NetworkNode(node_data)
        gfx_node.setPos(node_data.get('x', 0), node_data.get('y', 0))
        self._scene.addItem(gfx_node)
        self._nodes[node_data['ip']] = gfx_node
        return gfx_node

    def get_node(self, ip: str) -> Optional[NetworkNode]:
        return self._nodes.get(ip)

    def get_all_nodes(self) -> Dict[str, NetworkNode]:
        return dict(self._nodes)

    def auto_layout(self, gateway_ip: str = None):
        """Arrange nodes in a star/radial layout with gateway at center."""
        nodes = list(self._nodes.values())
        if not nodes:
            return

        # Clear existing edges
        for edge in self._edges:
            self._scene.removeItem(edge)
        self._edges.clear()

        # Find gateway node
        gw_node = None
        other_nodes = []
        for node in nodes:
            last_octet = node.data['ip'].split('.')[-1]
            if last_octet in ('1', '254') or node.data.get('device_type') == 'router':
                gw_node = node
            else:
                other_nodes.append(node)

        if gw_node is None and nodes:
            gw_node = nodes[0]
            other_nodes = nodes[1:]

        # Place gateway at center
        cx, cy = 0, 0
        if gw_node:
            gw_node.setPos(cx, cy)
            gw_node.data['x'] = cx
            gw_node.data['y'] = cy

        # Arrange others in concentric circles
        if other_nodes:
            ring_capacity = 8
            radius = 180
            for i, node in enumerate(other_nodes):
                ring = i // ring_capacity
                pos_in_ring = i % ring_capacity
                total_in_ring = min(ring_capacity, len(other_nodes) - ring * ring_capacity)

                r = radius + ring * 140
                angle = (2 * math.pi * pos_in_ring / total_in_ring) - math.pi / 2
                nx = cx + r * math.cos(angle)
                ny = cy + r * math.sin(angle)
                node.setPos(nx, ny)
                node.data['x'] = nx
                node.data['y'] = ny

                # Draw edge to gateway
                if gw_node:
                    edge = QGraphicsLineItem(cx, cy, nx, ny)
                    edge.setPen(QPen(QColor(Colors.BORDER_LIGHT), 1, Qt.PenStyle.DotLine))
                    edge.setZValue(1)
                    self._scene.addItem(edge)
                    self._edges.append(edge)

    def fit_view(self):
        if self._nodes:
            rect = self._scene.itemsBoundingRect()
            rect.adjust(-60, -60, 60, 60)
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def export_to_image(self, path: str, width: int = 1920, height: int = 1080):
        """Export the current view to a PNG image."""
        rect = self._scene.itemsBoundingRect()
        rect.adjust(-40, -40, 40, 40)

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(Colors.BG))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._scene.render(painter, QRectF(0, 0, width, height), rect)
        painter.end()

        image.save(path)


class NodeDetailPanel(QFrame):
    """Detail panel for the selected node."""

    label_changed = Signal(str, str)  # ip, new_label

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"NodeDetailPanel {{ background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER}; border-radius: 8px; }}"
        )
        self.setFixedWidth(280)
        self._current_ip = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        self._title = QLabel(t("netmap.detail_ip"))
        self._title.setStyleSheet(
            f"font-size: {Fonts.SIZE_LG}px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        layout.addWidget(self._title)

        self._info_table = QTableWidget()
        self._info_table.setColumnCount(2)
        self._info_table.horizontalHeader().setVisible(False)
        self._info_table.verticalHeader().setVisible(False)
        self._info_table.setShowGrid(False)
        self._info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._info_table.setColumnWidth(0, 90)
        self._info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._info_table.setStyleSheet(
            f"QTableWidget {{ background-color: transparent; border: none; }} "
            f"QTableWidget::item {{ border: none; padding: 3px 4px; }}"
        )
        layout.addWidget(self._info_table, 1)

        btn_row = QHBoxLayout()
        self._label_btn = QPushButton(t("netmap.set_label"))
        self._label_btn.setFixedHeight(28)
        self._label_btn.clicked.connect(self._on_set_label)
        btn_row.addWidget(self._label_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._show_empty()

    def _show_empty(self):
        self._title.setText(t("dash.selected_device"))
        self._info_table.setRowCount(0)
        self._label_btn.setEnabled(False)

    def show_node(self, data: dict):
        self._current_ip = data.get('ip', '')
        display_name = data.get('user_label') or data.get('hostname') or data.get('ip', '')
        self._title.setText(display_name)

        online = data.get('online', True)
        status_text = t("netmap.online") if online else t("netmap.offline")
        status_color = Colors.CONNECTED if online else Colors.DISCONNECTED

        type_key = f"netmap.type_{data.get('device_type', 'unknown')}"

        rows = [
            (t("netmap.detail_ip"), data.get('ip', '')),
            (t("netmap.detail_hostname"), data.get('hostname', '') or '--'),
            (t("netmap.detail_mac"), data.get('mac', '') or '--'),
            (t("netmap.detail_rtt"), f"{data.get('rtt_ms', '--')} ms" if data.get('rtt_ms') is not None else '--'),
            (t("netmap.detail_type"), t(type_key)),
            (t("netmap.detail_status"), status_text),
            (t("netmap.detail_label"), data.get('user_label', '') or '--'),
        ]

        # Open ports
        ports = data.get('open_ports', [])
        if ports:
            rows.append((t("netmap.detail_ports"), ", ".join(str(p) for p in ports)))

        self._info_table.setRowCount(len(rows))
        for i, (key, val) in enumerate(rows):
            key_item = QTableWidgetItem(key)
            key_item.setForeground(QColor(Colors.TEXT_MUTED))
            key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._info_table.setItem(i, 0, key_item)

            val_item = QTableWidgetItem(str(val))
            val_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if key == t("netmap.detail_status"):
                val_item.setForeground(QColor(status_color))
            self._info_table.setItem(i, 1, val_item)

        self._label_btn.setEnabled(True)

    def _on_set_label(self):
        if not self._current_ip:
            return
        text, ok = QInputDialog.getText(
            self, t("netmap.set_label"), t("netmap.label_prompt"),
        )
        if ok:
            self.label_changed.emit(self._current_ip, text.strip())

    def retranslate(self):
        self._label_btn.setText(t("netmap.set_label"))


class NetworkMapPanel(QWidget):
    """Network Map panel — 10th tab."""

    def __init__(self, config_service, map_service: NetworkMapService, parent=None):
        super().__init__(parent)
        self._config_service = config_service
        self._map_service = map_service
        self._scan_worker = None
        self._ping_worker = None
        self._nodes: Dict[str, dict] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Title
        header = QHBoxLayout()
        self._title_label = QLabel(t("netmap.title"))
        self._title_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XL}px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        header.addWidget(self._title_label)
        header.addStretch()

        # Export buttons
        self._export_png_btn = QPushButton(t("netmap.export_png"))
        self._export_png_btn.setFixedHeight(30)
        self._export_png_btn.clicked.connect(self._export_png)
        header.addWidget(self._export_png_btn)

        self._export_csv_btn = QPushButton(t("netmap.export_csv"))
        self._export_csv_btn.setFixedHeight(30)
        self._export_csv_btn.clicked.connect(self._export_csv)
        header.addWidget(self._export_csv_btn)

        layout.addLayout(header)

        # Guide
        self._guide_label = QLabel(t("guide.networkmap"))
        self._guide_label.setWordWrap(True)
        self._guide_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_XS}px; color: {Colors.TEXT_MUTED}; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(self._guide_label)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        sub_label = QLabel(t("netmap.subnet"))
        sub_label.setStyleSheet(f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;")
        ctrl.addWidget(sub_label)
        self._sub_label = sub_label

        self._subnet_input = QLineEdit()
        self._subnet_input.setPlaceholderText("192.168.1")
        self._subnet_input.setFixedWidth(150)
        try:
            self._subnet_input.setText(get_local_subnet())
        except Exception:
            self._subnet_input.setText("192.168.1")
        ctrl.addWidget(self._subnet_input)

        self._scan_btn = QPushButton(t("netmap.scan"))
        self._scan_btn.setObjectName("btn_primary")
        self._scan_btn.setFixedHeight(32)
        self._scan_btn.clicked.connect(self._start_scan)
        ctrl.addWidget(self._scan_btn)

        self._stop_btn = QPushButton(t("netmap.stop"))
        self._stop_btn.setObjectName("btn_danger")
        self._stop_btn.setFixedHeight(32)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_scan)
        ctrl.addWidget(self._stop_btn)

        self._layout_btn = QPushButton(t("netmap.auto_layout"))
        self._layout_btn.setFixedHeight(32)
        self._layout_btn.clicked.connect(self._auto_layout)
        ctrl.addWidget(self._layout_btn)

        self._fit_btn = QPushButton(t("netmap.zoom_fit"))
        self._fit_btn.setFixedHeight(32)
        self._fit_btn.clicked.connect(self._fit_view)
        ctrl.addWidget(self._fit_btn)

        self._save_btn = QPushButton(t("netmap.save_layout"))
        self._save_btn.setFixedHeight(32)
        self._save_btn.clicked.connect(self._save_layout)
        ctrl.addWidget(self._save_btn)

        self._load_combo = QComboBox()
        self._load_combo.setFixedWidth(160)
        self._refresh_layout_combo()
        ctrl.addWidget(self._load_combo)

        self._load_btn = QPushButton(t("netmap.load_layout"))
        self._load_btn.setFixedHeight(32)
        self._load_btn.clicked.connect(self._load_layout)
        ctrl.addWidget(self._load_btn)

        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Progress
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SM}px; color: {Colors.TEXT_DIM}; background: transparent;"
        )
        layout.addWidget(self._status_label)

        # Main content: topology view + detail panel
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; width: 4px; }")

        self._topo_view = TopologyView()
        self._topo_view.node_clicked.connect(self._on_node_clicked)
        self._topo_view.node_double_clicked.connect(self._on_node_double_clicked)
        splitter.addWidget(self._topo_view)

        self._detail_panel = NodeDetailPanel()
        self._detail_panel.label_changed.connect(self._on_label_changed)
        splitter.addWidget(self._detail_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        layout.addWidget(splitter, 1)

    # ── Scan ──

    def _start_scan(self):
        import re
        subnet = self._subnet_input.text().strip()
        if not subnet:
            return
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}$', subnet):
            self._status_label.setText(t("netmap.invalid_subnet"))
            return

        self._topo_view.clear_all()
        self._nodes.clear()
        self._scan_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._progress.setVisible(True)
        self._progress.setMaximum(254)
        self._progress.setValue(0)
        self._status_label.setText(t("netmap.scanning"))

        from desktop.workers.network_map_worker import MapScanWorkerThread
        self._scan_worker = MapScanWorkerThread(subnet)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.node_found.connect(self._on_node_found)
        self._scan_worker.complete.connect(self._on_scan_complete)
        self._scan_worker.start()

    def _stop_scan(self):
        if self._scan_worker:
            self._scan_worker.stop()

    def _on_scan_progress(self, scanned, total):
        self._progress.setMaximum(total)
        self._progress.setValue(scanned)

    def _on_node_found(self, node_data: dict):
        ip = node_data['ip']
        self._nodes[ip] = node_data
        self._topo_view.add_node(node_data)

    def _on_scan_complete(self, all_nodes: list):
        self._scan_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress.setVisible(False)
        self._scan_worker = None

        count = len(all_nodes)
        if count == 0:
            self._status_label.setText(t("netmap.no_hosts"))
            return

        self._status_label.setText(t("netmap.scan_complete", count=count))
        self._auto_layout()
        self._fit_view()
        self._start_monitoring()

    # ── Monitoring ──

    def _start_monitoring(self):
        if self._ping_worker:
            self._ping_worker.stop()
            self._ping_worker.wait(2000)

        from desktop.workers.network_map_worker import MapPingWorkerThread
        self._ping_worker = MapPingWorkerThread(interval=10)
        ips = list(self._nodes.keys())
        self._ping_worker.set_ips(ips)
        self._ping_worker.update.connect(self._on_ping_update)
        self._ping_worker.start()
        self._status_label.setText(t("netmap.monitoring", count=len(ips)))

    def _on_ping_update(self, results: list):
        for r in results:
            ip = r['ip']
            gfx = self._topo_view.get_node(ip)
            if gfx:
                gfx.set_online(r['online'])
                gfx.update_rtt(r.get('rtt_ms'))
                if ip in self._nodes:
                    self._nodes[ip]['online'] = r['online']
                    self._nodes[ip]['rtt_ms'] = r.get('rtt_ms')

    # ── Node interaction ──

    def _on_node_clicked(self, data: dict):
        self._detail_panel.show_node(data)

    def _on_node_double_clicked(self, data: dict):
        ip = data.get('ip', '')
        current_label = data.get('user_label', '')
        text, ok = QInputDialog.getText(
            self, t("netmap.set_label"), t("netmap.label_prompt"),
            text=current_label,
        )
        if ok:
            self._on_label_changed(ip, text.strip())

    def _on_label_changed(self, ip: str, label: str):
        gfx = self._topo_view.get_node(ip)
        if gfx:
            gfx.set_label(label)
        if ip in self._nodes:
            self._nodes[ip]['user_label'] = label
        self._detail_panel.show_node(self._nodes.get(ip, {}))

    # ── Layout ──

    def _auto_layout(self):
        self._topo_view.auto_layout()

    def _fit_view(self):
        self._topo_view.fit_view()

    def _save_layout(self):
        name, ok = QInputDialog.getText(
            self, t("netmap.save_layout"),
            t("netmap.label_prompt"),
            text="vessel_layout",
        )
        if not ok or not name.strip():
            return

        # Collect current node states with positions
        nodes = []
        for ip, gfx_node in self._topo_view.get_all_nodes().items():
            pos = gfx_node.pos()
            data = dict(gfx_node.data)
            data['x'] = pos.x()
            data['y'] = pos.y()
            nodes.append(MapNode.from_dict(data))

        path = self._map_service.save_layout(name.strip(), nodes)
        self._refresh_layout_combo()
        self._status_label.setText(t("netmap.layout_saved", path=os.path.basename(path)))

    def _load_layout(self):
        filename = self._load_combo.currentData()
        if not filename:
            return

        nodes = self._map_service.load_layout(filename)
        if not nodes:
            return

        self._topo_view.clear_all()
        self._nodes.clear()

        for node in nodes:
            data = node.to_dict()
            self._nodes[data['ip']] = data
            self._topo_view.add_node(data)

        self._fit_view()
        self._start_monitoring()
        self._status_label.setText(t("netmap.layout_loaded", count=len(nodes)))

    def _refresh_layout_combo(self):
        self._load_combo.clear()
        self._load_combo.addItem("--", "")
        for layout in self._map_service.list_layouts():
            label = f"{layout['name']} ({layout['node_count']})"
            self._load_combo.addItem(label, layout['filename'])

    # ── Export ──

    def _export_png(self):
        if not self._nodes:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(t("common.export"), t("netmap.no_hosts"), confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
            return

        path, _ = QFileDialog.getSaveFileName(
            self, t("netmap.export_png"), "network_map.png", "PNG Files (*.png)"
        )
        if path:
            self._topo_view.export_to_image(path)
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(t("common.export"), f"Exported: {os.path.basename(path)}", confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
    def _export_csv(self):
        if not self._nodes:
            from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

            ConfirmDialog(t("common.export"), t("netmap.no_hosts"), confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
            return

        path, _ = QFileDialog.getSaveFileName(
            self, t("netmap.export_csv"), "network_map.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["IP", "Hostname", "MAC", "RTT (ms)", "Open Ports", "Type", "Label", "Status"])
            for ip in sorted(self._nodes.keys(), key=lambda x: list(map(int, x.split('.')))):
                n = self._nodes[ip]
                writer.writerow([
                    n.get('ip', ''),
                    n.get('hostname', ''),
                    n.get('mac', ''),
                    n.get('rtt_ms', ''),
                    ", ".join(str(p) for p in n.get('open_ports', [])),
                    n.get('device_type', ''),
                    n.get('user_label', ''),
                    t("netmap.online") if n.get('online') else t("netmap.offline"),
                ])
        from geoview_pyside6.widgets.confirm_dialog import ConfirmDialog

        ConfirmDialog(t("common.export"), f"Exported: {os.path.basename(path)}", confirm_text="OK", cancel_text="", dialog_type="success", parent=self).exec()
    # ── Retranslate ──

    def retranslate(self):
        self._title_label.setText(t("netmap.title"))
        self._guide_label.setText(t("guide.networkmap"))
        self._sub_label.setText(t("netmap.subnet"))
        self._scan_btn.setText(t("netmap.scan"))
        self._stop_btn.setText(t("netmap.stop"))
        self._layout_btn.setText(t("netmap.auto_layout"))
        self._fit_btn.setText(t("netmap.zoom_fit"))
        self._save_btn.setText(t("netmap.save_layout"))
        self._load_btn.setText(t("netmap.load_layout"))
        self._export_png_btn.setText(t("netmap.export_png"))
        self._export_csv_btn.setText(t("netmap.export_csv"))
        self._detail_panel.retranslate()

    # ── Cleanup ──

    def stop_workers(self):
        if self._scan_worker:
            self._scan_worker.stop()
            self._scan_worker.wait(3000)
        if self._ping_worker:
            self._ping_worker.stop()
            self._ping_worker.wait(3000)

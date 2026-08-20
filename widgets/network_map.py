#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Network Map Widget - Visualisasi Session dengan Logo OS
FIX: Beacon + OS detection akurat
"""

import math
import time
import platform
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsItem,
    QGraphicsPathItem, QMenu, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QPen, QFont, QPainter, QPainterPath,
    QPixmap, QAction, QCursor
)


class DynamicConnectionLine(QGraphicsLineItem):
    def __init__(self, from_node, to_node, color="#00ff00", parent=None):
        super().__init__(parent)
        self.from_node = from_node
        self.to_node = to_node
        self.base_color = QColor(color)
        self.is_active = True
        self.label_item = None
        self.label_bg = None
        
        pen = QPen(self.base_color, 1.5)
        pen.setStyle(Qt.PenStyle.SolidLine)
        self.setPen(pen)
        self.setZValue(0)
        
        self.from_node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.to_node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.update_position()
    
    def update_position(self):
        if not self.from_node or not self.to_node:
            return
        try:
            from_rect = self.from_node.sceneBoundingRect()
            to_rect = self.to_node.sceneBoundingRect()
            from_x = from_rect.center().x()
            from_y = from_rect.center().y()
            to_x = to_rect.center().x()
            to_y = to_rect.center().y()
            self.setLine(from_x, from_y, to_x, to_y)
            
            if self.label_item and self.label_bg:
                mid_x = (from_x + to_x) / 2
                mid_y = (from_y + to_y) / 2 - 15
                self.label_bg.setPos(mid_x - 30, mid_y - 8)
                self.label_item.setPos(
                    mid_x - self.label_item.boundingRect().width() / 2,
                    mid_y - self.label_item.boundingRect().height() / 2
                )
        except Exception:
            pass
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.update_position()
        return super().itemChange(change, value)
    
    def set_active(self, active):
        self.is_active = active
        if active:
            pen = QPen(self.base_color, 1.5)
            pen.setStyle(Qt.PenStyle.SolidLine)
            self.setPen(pen)
        else:
            pen = QPen(QColor("#666666"), 1)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([6, 6])
            self.setPen(pen)
    
    def set_label(self, text, color="#00ff00"):
        if self.label_item:
            if self.label_item.scene():
                self.label_item.scene().removeItem(self.label_item)
            self.label_item = None
        if self.label_bg:
            if self.label_bg.scene():
                self.label_bg.scene().removeItem(self.label_bg)
            self.label_bg = None
        if not text:
            return
        self.label_bg = QGraphicsRectItem(0, 0, 60, 16)
        self.label_bg.setBrush(QBrush(QColor("#1a1a1a")))
        self.label_bg.setPen(QPen(QColor(color), 1))
        self.label_bg.setZValue(1)
        self.label_item = QGraphicsTextItem(text.upper())
        self.label_item.setDefaultTextColor(QColor(color))
        self.label_item.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        self.label_item.setZValue(2)
        if self.scene():
            self.scene().addItem(self.label_bg)
            self.scene().addItem(self.label_item)
        self.update_position()
    
    def stop(self):
        if self.label_item and self.label_item.scene():
            self.label_item.scene().removeItem(self.label_item)
        if self.label_bg and self.label_bg.scene():
            self.label_bg.scene().removeItem(self.label_bg)
        if self.scene():
            self.scene().removeItem(self)


class NetworkMapWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)

        self.view.setBackgroundBrush(QBrush(QColor("#0c0c0c")))
        self.scene.setBackgroundBrush(QBrush(QColor("#0c0c0c")))
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setInteractive(True)

        self.view.setStyleSheet("""
            QGraphicsView {
                border: 1px solid #1e1e1e;
                border-radius: 4px;
                background: #0c0c0c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_map)
        self.timer.start(3000)
        self.is_running = True

        self.nodes = {}
        self.node_items = {}
        self.connection_lines = []
        self.animated_items = []
        self.timers = []
        self.custom_positions = {}

        # ===== OS IMAGE SEARCH PATHS =====
        self.image_search_paths = [
            Path(__file__).resolve().parent.parent / 'assets' / 'os',
            Path(__file__).resolve().parent.parent / 'assets' / 'images' / 'os',
            Path(__file__).resolve().parent.parent / 'assets' / 'icons' / 'os',
            Path.cwd() / 'assets' / 'os',
            Path.cwd() / 'images' / 'os',
            Path(__file__).resolve().parent.parent / 'banner' / 'os',
            Path.home() / '.lazyframework' / 'assets' / 'os',
            Path('/usr/share/lazyframework/assets/os'),
            Path('/usr/share/lazyframework/resources/os_images'),
        ]

        # ===== OS NAME → IMAGE FILENAME MAPPING =====
        self.os_image_map = {
            'kali': ['kali', 'linux'],
            'linux': ['linux', 'kali'],
            'windows': ['windows', 'win'],
            'ubuntu': ['ubuntu', 'linux'],
            'debian': ['debian', 'linux'],
            'fedora': ['fedora', 'linux'],
            'arch': ['arch', 'linux'],
            'centos': ['centos', 'linux'],
            'parrot': ['parrot', 'linux'],
            'macos': ['macos', 'mac', 'darwin'],
            'darwin': ['macos'],
            'freebsd': ['freebsd', 'bsd'],
            'linux': ['linux'],
            'unknown': ['unknown', 'linux'],
            'android': ['android'],
            'ios': ['ios'],
            'server': ['server', 'windows_server'],
        }

        # ===== EMOTICON FALLBACK =====
        self.os_emoji_map = {
            'kali': '🐉',
            'windows': '🪟',
            'ubuntu': '🔶',
            'debian': '🌀',
            'fedora': '🔵',
            'arch': '🔺',
            'centos': '🔷',
            'parrot': '🦜',
            'macos': '🍎',
            'darwin': '🍎',
            'freebsd': '🐋',
            'linux': '🐧',
            'unknown': '💻',
            'android': '🤖',
            'ios': '📱',
            'server': '🖥️',
        }

        # ===== OS COLORS =====
        self.os_color_map = {
            'kali': '#336699',
            'windows': '#4a90e2',
            'ubuntu': '#dd4814',
            'debian': '#a53860',
            'fedora': '#003478',
            'arch': '#1793d1',
            'centos': '#922b7a',
            'parrot': '#4caf50',
            'macos': '#ff9500',
            'darwin': '#ff9500',
            'freebsd': '#ab2b1d',
            'linux': '#34c759',
            'unknown': '#8e8e93',
            'android': '#3ddc84',
            'ios': '#007aff',
            'server': '#2b6cb0',
        }

        self.host_os = self._detect_host_os()
        self.image_cache = {}
        self._last_refresh_time = 0
        
        print(f"[*] NetworkMap initialized, host OS: {self.host_os}")

    # ─────────────────────────────────────────────────────────────
    # OS DETECTION HOST
    # ─────────────────────────────────────────────────────────────

    def _detect_host_os(self):
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'kali' in content:
                        return 'kali'
                    elif 'ubuntu' in content:
                        return 'ubuntu'
                    elif 'debian' in content:
                        return 'debian'
                    elif 'fedora' in content:
                        return 'fedora'
                    elif 'arch' in content:
                        return 'arch'
                    elif 'centos' in content:
                        return 'centos'
                    elif 'parrot' in content:
                        return 'parrot'
        except:
            pass

        system = platform.system().lower()
        if 'windows' in system:
            return 'windows'
        elif 'darwin' in system:
            return 'macos'
        else:
            return 'linux'

    # ─────────────────────────────────────────────────────────────
    # GET OS TYPE DARI SESSION - FIXED
    # ─────────────────────────────────────────────────────────────

    def get_session_os(self, session_data):
        """
        Ambil OS dari session data dengan prioritas:
        1. os field di session_data
        2. handler.os
        3. handler.get('os')
        4. Fallback ke 'unknown'
        """
        # 1. Dari session data
        os_type = session_data.get('os', '')
        if os_type and os_type != 'unknown' and os_type != '':
            print(f"    OS from session: {os_type}")
            return os_type.lower()
        
        # 2. Dari handler
        handler = session_data.get('handler')
        if handler:
            if hasattr(handler, 'os'):
                val = handler.os
                if val and val != 'unknown':
                    print(f"    OS from handler.os: {val}")
                    return str(val).lower()
            if hasattr(handler, 'os_type'):
                val = handler.os_type
                if val and val != 'unknown':
                    print(f"    OS from handler.os_type: {val}")
                    return str(val).lower()
            if hasattr(handler, 'get') and callable(handler.get):
                val = handler.get('os')
                if val and val != 'unknown':
                    print(f"    OS from handler.get('os'): {val}")
                    return str(val).lower()
                val = handler.get('os_type')
                if val and val != 'unknown':
                    print(f"    OS from handler.get('os_type'): {val}")
                    return str(val).lower()
        
        # 3. Dari data lainnya
        for key in ['ostype', 'platform', 'system', 'target_os', 'type']:
            val = session_data.get(key)
            if val and val != 'unknown':
                print(f"    OS from {key}: {val}")
                return str(val).lower()
        
        print(f"    OS: unknown (no data)")
        return 'unknown'

    # ─────────────────────────────────────────────────────────────
    # FIND OS IMAGE - EXACT MATCH
    # ─────────────────────────────────────────────────────────────

    def find_os_image(self, os_type):
        os_type = (os_type or 'unknown').lower().strip()
        
        cache_key = os_type
        if cache_key in self.image_cache:
            cached = self.image_cache[cache_key]
            if cached and os.path.exists(cached):
                return cached
            del self.image_cache[cache_key]
        
        possible_names = self.os_image_map.get(os_type, [os_type])
        extensions = ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']
        
        for search_path in self.image_search_paths:
            if not search_path.exists():
                continue
            for name in possible_names:
                for ext in extensions:
                    image_file = search_path / f'{name}{ext}'
                    if image_file.exists():
                        # VERIFY: Jangan ambil file yang salah
                        stem = image_file.stem.lower()
                        if os_type == 'kali' and 'windows' in stem:
                            continue
                        if os_type == 'windows' and 'kali' in stem:
                            continue
                        if os_type == 'arch' and 'kali' in stem:
                            continue
                        if os_type == 'ubuntu' and 'kali' in stem:
                            continue
                        if os_type == 'debian' and 'kali' in stem:
                            continue
                        
                        self.image_cache[cache_key] = str(image_file)
                        print(f"[+] Found EXACT OS image: {image_file} for OS: {os_type}")
                        return str(image_file)
        
        # Fallback partial
        for search_path in self.image_search_paths:
            if not search_path.exists():
                continue
            for name in possible_names:
                for ext in extensions:
                    for img_file in search_path.glob(f'*{ext}'):
                        stem = img_file.stem.lower()
                        if name.lower() in stem:
                            if os_type == 'kali' and 'windows' in stem:
                                continue
                            if os_type == 'windows' and 'kali' in stem:
                                continue
                            if os_type == 'arch' and 'kali' in stem:
                                continue
                            self.image_cache[cache_key] = str(img_file)
                            print(f"[+] Found OS image (partial): {img_file} for OS: {os_type}")
                            return str(img_file)
        
        self.image_cache[cache_key] = None
        print(f"[!] No image found for OS: {os_type}, using emoji")
        return None

    def get_os_icon(self, os_type):
        os_type = (os_type or 'unknown').lower().strip()
        return self.os_emoji_map.get(os_type, '💻')

    def get_os_color(self, os_type):
        os_type = (os_type or 'unknown').lower().strip()
        return self.os_color_map.get(os_type, '#8e8e93')

    # ─────────────────────────────────────────────────────────────
    # CREATE COMPUTER ICON
    # ─────────────────────────────────────────────────────────────

    def create_computer_icon(self, x, y, os_type="unknown", is_server=False,
                             monitor_width=160, monitor_height=110,
                             is_active=True, session_id=None):
        os_type = (os_type or 'unknown').lower().strip()
        accent = self.get_os_color(os_type)
        emoji = self.get_os_icon(os_type)
        
        image_path = None
        if is_server:
            image_path = self.find_os_image('server')
            if not image_path:
                image_path = self.find_os_image(os_type)
        else:
            image_path = self.find_os_image(os_type)
        
        bezel = 6
        screen_w = monitor_width - bezel * 2
        screen_h = monitor_height - bezel * 2 - 4
        
        mon_x = x - monitor_width // 2
        mon_y = y - monitor_height // 2
        
        if not is_server and is_active:
            glow_outer = QGraphicsRectItem(
                mon_x - 4, mon_y - 4,
                monitor_width + 8, monitor_height + 8
            )
            glow_outer.setBrush(QBrush(QColor(255, 0, 0, 15)))
            glow_outer.setPen(QPen(QColor(255, 0, 0, 60), 2))
            glow_outer.setZValue(-1)
            self.scene.addItem(glow_outer)
            
            glow_inner = QGraphicsRectItem(
                mon_x - 2, mon_y - 2,
                monitor_width + 4, monitor_height + 4
            )
            glow_inner.setBrush(QBrush(QColor(255, 0, 0, 8)))
            glow_inner.setPen(QPen(QColor(255, 50, 50, 100), 1.5))
            glow_inner.setZValue(-1)
            self.scene.addItem(glow_inner)
        
        body = QGraphicsRectItem(mon_x, mon_y, monitor_width, monitor_height)
        body.setBrush(QBrush(QColor("#1a1a1a")))
        body.setPen(QPen(QColor("#0d0d0d"), 1.5))
        self.scene.addItem(body)
        
        top_highlight = QGraphicsRectItem(mon_x + 2, mon_y + 2, monitor_width - 4, 2)
        top_highlight.setBrush(QBrush(QColor("#2a2a2a")))
        top_highlight.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(top_highlight)
        
        screen_rect = QRectF(mon_x + bezel, mon_y + bezel, screen_w, screen_h)
        screen = QGraphicsRectItem(screen_rect)
        screen.setBrush(QBrush(QColor("#0a0a0a")))
        screen.setPen(QPen(QColor("#111111"), 1))
        self.scene.addItem(screen)
        
        image_displayed = False
        if image_path and os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        int(screen_w - 10),
                        int(screen_h - 10),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    img_item = QGraphicsPixmapItem(scaled)
                    img_item.setPos(
                        screen_rect.x() + (screen_w - scaled.width()) / 2,
                        screen_rect.y() + (screen_h - scaled.height()) / 2
                    )
                    self.scene.addItem(img_item)
                    image_displayed = True
            except Exception as e:
                print(f"[!] Failed to load image: {e}")
        
        if not image_displayed:
            icon_text = QGraphicsTextItem(emoji)
            icon_text.setDefaultTextColor(QColor(accent))
            icon_text.setFont(QFont("Segoe UI Emoji", 18))
            icon_text.setPos(
                screen_rect.x() + (screen_w - icon_text.boundingRect().width()) / 2,
                screen_rect.y() + (screen_h - icon_text.boundingRect().height()) / 2 - 8
            )
            self.scene.addItem(icon_text)
            
            os_display = os_type.upper() if os_type != 'unknown' else 'PC'
            if os_display == 'DARWIN':
                os_display = 'macOS'
            elif os_display == 'WINDOWS_SERVER':
                os_display = 'SERVER'
            elif os_display == 'KALI':
                os_display = 'KALI'
            
            os_text = QGraphicsTextItem(os_display)
            os_text.setDefaultTextColor(QColor(accent))
            os_text.setFont(QFont("Consolas", 6, QFont.Weight.Bold))
            os_text.setPos(
                screen_rect.x() + (screen_w - os_text.boundingRect().width()) / 2,
                screen_rect.y() + (screen_h - os_text.boundingRect().height()) / 2 + 16
            )
            self.scene.addItem(os_text)
        
        if not is_server:
            status_color = "#00ff00" if is_active else "#ff4444"
            status_dot = QGraphicsEllipseItem(
                mon_x + monitor_width - 12,
                mon_y + 4,
                6, 6
            )
            status_dot.setBrush(QBrush(QColor(status_color)))
            status_dot.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(status_dot)
        
        neck_w = 8
        neck_h = 14
        neck = QGraphicsRectItem(
            x - neck_w // 2,
            mon_y + monitor_height - 2,
            neck_w,
            neck_h
        )
        neck.setBrush(QBrush(QColor("#1f1f1f")))
        neck.setPen(QPen(QColor("#0d0d0d"), 1))
        self.scene.addItem(neck)
        
        stand_top_y = mon_y + monitor_height + neck_h - 2
        stand_w = 50
        stand_h = 10
        path = QPainterPath()
        path.moveTo(x, stand_top_y)
        path.lineTo(x - stand_w // 2, stand_top_y + stand_h)
        path.lineTo(x + stand_w // 2, stand_top_y + stand_h)
        path.closeSubpath()
        stand = QGraphicsPathItem(path)
        stand.setBrush(QBrush(QColor("#1a1a1a")))
        stand.setPen(QPen(QColor("#0d0d0d"), 1))
        self.scene.addItem(stand)
        
        body.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        body.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        body.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        body.setCursor(Qt.CursorShape.OpenHandCursor)
        
        if session_id:
            body.setData(0, session_id)
        else:
            body.setData(0, "teamserver")
        
        return body

    # ─────────────────────────────────────────────────────────────
    # BEACON ITEM - FIXED: Tampilkan OS yang benar
    # ─────────────────────────────────────────────────────────────

    def create_beacon_item(self, x, y, text, color="#00ff00", is_beacon=True, os_type="unknown"):
        """
        Buat beacon dengan OS icon yang benar
        """
        os_type = (os_type or 'unknown').lower().strip()
        emoji = self.get_os_icon(os_type)
        accent = self.get_os_color(os_type)
        
        if is_beacon:
            outer = QGraphicsEllipseItem(x - 20, y - 20, 40, 40)
            outer.setBrush(QBrush(QColor(color + "20")))
            outer.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(outer)

        circle = QGraphicsEllipseItem(x - 16, y - 16, 32, 32)
        circle.setBrush(QBrush(QColor("#1a1a1a")))
        circle.setPen(QPen(QColor(accent), 2))
        self.scene.addItem(circle)

        # Tampilkan emoji OS di beacon
        icon = QGraphicsTextItem(emoji)
        icon.setDefaultTextColor(QColor(accent))
        icon.setFont(QFont("Segoe UI Emoji", 12))
        icon.setPos(x - icon.boundingRect().width() / 2, y - icon.boundingRect().height() / 2)
        self.scene.addItem(icon)

        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(QColor("#cccccc"))
        text_item.setFont(QFont("Consolas", 8))
        text_item.setPos(x - text_item.boundingRect().width() / 2, y + 20)
        self.scene.addItem(text_item)

        return circle

    # ─────────────────────────────────────────────────────────────
    # REFRESH MAP
    # ─────────────────────────────────────────────────────────────

    def refresh_map(self):
        try:
            if hasattr(self, '_last_refresh_time'):
                current = time.time()
                if current - self._last_refresh_time < 0.5:
                    return
                self._last_refresh_time = current
            self._refresh_map_impl()
        except Exception as e:
            print(f"[ERROR] refresh_map: {e}")

    def _refresh_map_impl(self):
        try:
            self._save_current_positions()
            self.cleanup()
            self.scene.clear()
            self.nodes.clear()
            self.node_items.clear()
            self.connection_lines.clear()
            self.animated_items = []

            self.draw_cobalt_strike_background()

            PC_WIDTH = 160
            PC_HEIGHT = 110
            PC_INFO_HEIGHT = 55
            PC_TOTAL_HEIGHT = PC_HEIGHT + PC_INFO_HEIGHT + 12

            header = QGraphicsTextItem("LAZY FRAMEWORK - TEAM SERVER")
            header.setDefaultTextColor(QColor("#00ff00"))
            header.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
            header.setPos(-header.boundingRect().width() / 2, -480)
            self.scene.addItem(header)

            subtitle = QGraphicsTextItem("Network Visualization & Session Management")
            subtitle.setDefaultTextColor(QColor("#cccccc"))
            subtitle.setFont(QFont("Consolas", 10))
            subtitle.setPos(-subtitle.boundingRect().width() / 2, -450)
            self.scene.addItem(subtitle)

            separator = QGraphicsLineItem(-600, -430, 600, -430)
            separator.setPen(QPen(QColor("#333333"), 1))
            self.scene.addItem(separator)

            # ── Team Server ──
            attacker_x = -400
            attacker_y = -250

            if "teamserver" in self.custom_positions:
                attacker_x, attacker_y = self.custom_positions["teamserver"]

            server_os = self.host_os

            server_pc = self.create_computer_icon(
                attacker_x, attacker_y,
                os_type=server_os,
                is_server=True,
                monitor_width=PC_WIDTH,
                monitor_height=PC_HEIGHT,
                is_active=False
            )

            server_label = QGraphicsTextItem("⚡ TEAM SERVER")
            server_label.setDefaultTextColor(QColor("#ff6b00"))
            server_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            server_label.setPos(
                attacker_x - server_label.boundingRect().width() / 2,
                attacker_y + (PC_HEIGHT // 2) + 32
            )
            self.scene.addItem(server_label)

            server_info = QGraphicsTextItem(
                f"@{self.parent.framework.session.get('user', 'unknown')}\n"
                f"{self.parent.framework.session.get('LHOST', '0.0.0.0')}:"
                f"{self.parent.framework.session.get('LPORT', '4444')}"
            )
            server_info.setDefaultTextColor(QColor("#666666"))
            server_info.setFont(QFont("Consolas", 7))
            server_info.setPos(
                attacker_x - server_info.boundingRect().width() / 2,
                attacker_y + (PC_HEIGHT // 2) + 48
            )
            self.scene.addItem(server_info)

            self.nodes["teamserver"] = {'item': server_pc, 'x': attacker_x, 'y': attacker_y, 'type': 'server'}
            self.node_items["teamserver"] = server_pc

            def make_ts_right_click(event):
                if event.button() == Qt.MouseButton.RightButton:
                    self._show_teamserver_context_menu(event)
                    event.accept()
                else:
                    QGraphicsRectItem.mousePressEvent(server_pc, event)

            server_pc.mousePressEvent = make_ts_right_click

            # ── Listeners ──
            listener_x_start = -150
            listener_y = attacker_y + 30

            active_listeners = []
            if hasattr(self.parent, 'active_listeners'):
                with self.parent.listener_lock:
                    if isinstance(self.parent.active_listeners, list):
                        active_listeners = list(self.parent.active_listeners)
                    elif isinstance(self.parent.active_listeners, dict):
                        active_listeners = list(self.parent.active_listeners.values())

            listener_nodes = []
            for idx, listener in enumerate(active_listeners):
                if isinstance(listener, dict):
                    lhost = listener.get("lhost", "0.0.0.0")
                    lport = listener.get("lport", "4444")
                else:
                    lhost = "0.0.0.0"
                    lport = "4444"
                key = f"listener:{lhost}:{lport}"

                listener_x = listener_x_start + idx * 100

                beacon = self.create_beacon_item(
                    listener_x, listener_y,
                    f"LISTENER\n{lport}",
                    "#ff4444",
                    is_beacon=True,
                    os_type="server"
                )

                details = QGraphicsTextItem(f"{lhost}")
                details.setDefaultTextColor(QColor("#888888"))
                details.setFont(QFont("Consolas", 7))
                details.setPos(
                    listener_x - details.boundingRect().width() / 2,
                    listener_y + 42
                )
                self.scene.addItem(details)

                self.nodes[key] = {'item': beacon, 'x': listener_x, 'y': listener_y, 'type': 'listener'}
                self.node_items[key] = beacon
                listener_nodes.append(key)

                self.add_connection("teamserver", key, f"handler {idx + 1}", is_active=False)

            # ── Sessions ──
            session_x_start = 180
            session_y_start = attacker_y - (PC_HEIGHT // 2) + 30

            sessions_count = len(self.parent.sessions) if hasattr(self.parent, 'sessions') else 0
            print(f"[+] NetworkMap: {sessions_count} sessions detected")

            if sessions_count == 0:
                no_sess = QGraphicsTextItem("No active sessions\nStart a reverse_tcp listener first")
                no_sess.setDefaultTextColor(QColor("#666666"))
                no_sess.setFont(QFont("Consolas", 12))
                no_sess.setPos(-no_sess.boundingRect().width() / 2, 50)
                self.scene.addItem(no_sess)
                return

            session_nodes = []
            for idx, (sid, sess) in enumerate(self.parent.sessions.items()):
                # ===== AMBIL OS DENGAN BENAR =====
                os_type = self.get_session_os(sess)
                
                print(f"    Session {sid}: OS={os_type}")

                status = sess.get("status", "alive")
                is_active = (status == "alive")

                row = idx // 4
                col = idx % 4
                session_x = session_x_start + col * 150
                session_y = session_y_start + row * (PC_TOTAL_HEIGHT + 25)

                if sid in self.custom_positions:
                    session_x, session_y = self.custom_positions[sid]

                # ===== BUAT IKON DENGAN OS YANG BENAR =====
                computer = self.create_computer_icon(
                    session_x, session_y,
                    os_type=os_type,
                    is_server=False,
                    monitor_width=PC_WIDTH,
                    monitor_height=PC_HEIGHT,
                    is_active=is_active,
                    session_id=sid
                )

                info_top = session_y + (PC_HEIGHT // 2) + 32

                info_bg = QGraphicsRectItem(
                    session_x - 60,
                    info_top,
                    120,
                    PC_INFO_HEIGHT
                )
                info_bg.setBrush(QBrush(QColor("#1a1a1a")))
                info_bg.setPen(QPen(QColor("#333333"), 1))
                self.scene.addItem(info_bg)

                session_id_text = QGraphicsTextItem(f"#{idx + 1} {sid[:8]}")
                session_id_text.setDefaultTextColor(QColor("#00ff00"))
                session_id_text.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                session_id_text.setPos(
                    session_x - session_id_text.boundingRect().width() / 2,
                    info_top + 4
                )
                self.scene.addItem(session_id_text)

                details = QGraphicsTextItem(
                    f"{sess.get('ip', '?.?.?.?')}:{sess.get('port', '?')}\n"
                    f"{sess.get('type', 'shell')}"
                )
                details.setDefaultTextColor(QColor("#cccccc"))
                details.setFont(QFont("Consolas", 7))
                details.setPos(
                    session_x - details.boundingRect().width() / 2,
                    info_top + 20
                )
                self.scene.addItem(details)

                status_text = "ALIVE" if is_active else "DEAD"
                status_color = "#00ff00" if is_active else "#ff4444"
                status_item = QGraphicsTextItem(f"● {status_text}")
                status_item.setDefaultTextColor(QColor(status_color))
                status_item.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                status_item.setPos(
                    session_x + (PC_WIDTH // 2) - 8,
                    session_y - (PC_HEIGHT // 2) - 14
                )
                self.scene.addItem(status_item)

                self.nodes[sid] = {'item': computer, 'x': session_x, 'y': session_y, 'type': 'session'}
                self.node_items[sid] = computer
                session_nodes.append(sid)

                if listener_nodes:
                    listener_key = listener_nodes[-1] if listener_nodes else None
                    if listener_key:
                        self.add_connection(
                            listener_key, sid,
                            f"beacon {idx + 1}",
                            is_active=is_active
                        )

                def make_double_click(session_id):
                    def handler(event):
                        if event.button() == Qt.MouseButton.LeftButton:
                            if hasattr(self.parent, 'interact_with_session'):
                                self.parent.interact_with_session(session_id)
                    return handler

                computer.mouseDoubleClickEvent = make_double_click(sid)

                def make_mouse_press(session_id):
                    def handler(event):
                        if event.button() == Qt.MouseButton.RightButton:
                            self._show_session_context_menu(session_id, event)
                            event.accept()
                        else:
                            QGraphicsRectItem.mousePressEvent(computer, event)
                    return handler

                computer.mousePressEvent = make_mouse_press(sid)
                computer.setCursor(Qt.CursorShape.OpenHandCursor)

            # ── Footer ──
            footer_bg = QGraphicsRectItem(-600, 430, 1200, 50)
            footer_bg.setBrush(QBrush(QColor("#1a1a1a")))
            footer_bg.setPen(QPen(QColor("#333333"), 1))
            self.scene.addItem(footer_bg)

            stats = QGraphicsTextItem(
                f"📊 STATS | Listeners: {len(active_listeners)} • "
                f"Sessions: {len(self.parent.sessions)} • "
                f"Updated: {time.strftime('%H:%M:%S')}"
            )
            stats.setDefaultTextColor(QColor("#cccccc"))
            stats.setFont(QFont("Consolas", 9))
            stats.setPos(-stats.boundingRect().width() / 2, 445)
            self.scene.addItem(stats)

            legend_text = "🖥️ Team Server • 🔗 Listener • "
            if self.image_cache:
                image_count = sum(1 for v in self.image_cache.values() if v is not None)
                total = len(self.image_cache)
                if total > 0:
                    legend_text += f"📷 Images: {image_count}/{total} loaded • "
            legend_text += "Drag = pindah • Double-click = interact • Right-click = menu"

            legend = QGraphicsTextItem(legend_text)
            legend.setDefaultTextColor(QColor("#666666"))
            legend.setFont(QFont("Consolas", 8))
            legend.setPos(-legend.boundingRect().width() / 2, 468)
            self.scene.addItem(legend)

        except Exception as e:
            print(f"[!] NetworkMap refresh error: {e}")
            import traceback
            traceback.print_exc()

    def draw_cobalt_strike_background(self):
        grid_pen = QPen(QColor("#1a1a1a"), 1)
        for y in range(-500, 501, 50):
            line = QGraphicsLineItem(-700, y, 700, y)
            line.setPen(grid_pen)
            self.scene.addItem(line)
        for x in range(-700, 701, 50):
            line = QGraphicsLineItem(x, -500, x, 500)
            line.setPen(grid_pen)
            self.scene.addItem(line)

    def add_connection(self, from_key, to_key, label="", is_active=True):
        if from_key not in self.node_items or to_key not in self.node_items:
            return
        from_item = self.node_items[from_key]
        to_item = self.node_items[to_key]
        color = "#00ff00" if is_active else "#666666"
        line = DynamicConnectionLine(from_item, to_item, color)
        self.scene.addItem(line)
        if is_active:
            line.set_active(True)
            if label:
                line.set_label(label, "#00ff00")
        else:
            line.set_active(False)
        self.connection_lines.append(line)

    # ─────────────────────────────────────────────────────────────
    # TIMER CONTROL
    # ─────────────────────────────────────────────────────────────

    def stop_refresh(self):
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
            self.is_running = False

    def start_refresh(self):
        if not self.is_running and hasattr(self, 'timer'):
            self.timer.start(3000)
            self.is_running = True

    def force_refresh(self):
        try:
            self.image_cache.clear()
            self.cleanup()
            self._refresh_map_impl()
            print("[+] NetworkMap force refreshed")
        except Exception as e:
            print(f"[!] NetworkMap force refresh error: {e}")

    def cleanup(self):
        for line in self.connection_lines:
            try:
                line.stop()
            except Exception:
                pass
        self.connection_lines.clear()
        for timer in self.timers:
            try:
                if timer and timer.isActive():
                    timer.stop()
            except Exception:
                pass
        self.timers.clear()
        for item in self.animated_items[:]:
            try:
                if hasattr(item, 'stop_animation'):
                    item.stop_animation()
                if item and item.scene() is not None:
                    self.scene.removeItem(item)
            except Exception:
                pass
        self.animated_items.clear()
        self.nodes.clear()
        self.node_items.clear()

    def _save_current_positions(self):
        for key, data in self.nodes.items():
            item = data.get('item')
            if item is None:
                continue
            try:
                if item.scene() is not None:
                    center_x = data['x'] + item.pos().x()
                    center_y = data['y'] + item.pos().y()
                    self.custom_positions[key] = (center_x, center_y)
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────
    # CONTEXT MENUS
    # ─────────────────────────────────────────────────────────────

    def _menu_style(self):
        return """
            QMenu {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #007acc;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #3c3c3c;
                margin: 4px 8px;
            }
        """

    def _show_session_context_menu(self, session_id, event):
        menu = QMenu()
        menu.setStyleSheet(self._menu_style())

        sess = self.parent.sessions.get(session_id, {})
        ip = sess.get("ip", "?")
        os_type = self.get_session_os(sess)
        status = sess.get("status", "alive")

        emoji = self.get_os_icon(os_type)
        header = QAction(f"{emoji} {session_id[:12]}  •  {ip}  •  {os_type.upper()}", menu)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        act_interact = QAction("▶ Interact / Open Tab", menu)
        act_interact.triggered.connect(lambda: self._ctx_interact(session_id))
        menu.addAction(act_interact)

        act_kill = QAction("☠ Kill Session", menu)
        act_kill.triggered.connect(lambda: self._ctx_kill_session(session_id))
        menu.addAction(act_kill)

        menu.addSeparator()
        modules_menu = menu.addMenu("🧩 Modules")
        module_actions = [
            ("payload/reverse/reverse_tcp", "Reverse TCP Listener"),
            ("post/linux/gather/enum_system", "Enum System (Linux)"),
            ("post/windows/gather/enum_system", "Enum System (Windows)"),
        ]
        for mod_path, label in module_actions:
            act = QAction(label, modules_menu)
            act.triggered.connect(
                lambda checked=False, p=mod_path, sid=session_id: self._ctx_run_module(p, sid)
            )
            modules_menu.addAction(act)

        menu.addSeparator()
        act_copy_ip = QAction("📋 Copy IP", menu)
        act_copy_ip.triggered.connect(lambda: self._ctx_copy_text(ip))
        menu.addAction(act_copy_ip)

        act_copy_id = QAction("📋 Copy Session ID", menu)
        act_copy_id.triggered.connect(lambda: self._ctx_copy_text(session_id))
        menu.addAction(act_copy_id)

        menu.exec(event.screenPos())

    def _show_teamserver_context_menu(self, event):
        menu = QMenu()
        menu.setStyleSheet(self._menu_style())

        header = QAction("⚡ TEAM SERVER", menu)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        act_refresh = QAction("🔄 Refresh Map", menu)
        act_refresh.triggered.connect(self.force_refresh)
        menu.addAction(act_refresh)

        act_reset_pos = QAction("↺ Reset Positions", menu)
        act_reset_pos.triggered.connect(self._ctx_reset_positions)
        menu.addAction(act_reset_pos)

        menu.addSeparator()
        modules_menu = menu.addMenu("🧩 Quick Modules")
        quick = [
            ("payload/reverse/reverse_tcp", "Start Reverse TCP"),
            ("auxiliary/scanner/portscan/tcp", "TCP Port Scan"),
        ]
        for mod_path, label in quick:
            act = QAction(label, modules_menu)
            act.triggered.connect(lambda checked=False, p=mod_path: self._ctx_run_module(p, None))
            modules_menu.addAction(act)

        menu.exec(event.screenPos())

    def _ctx_interact(self, session_id):
        if hasattr(self.parent, "interact_with_session"):
            self.parent.interact_with_session(session_id)

    def _ctx_kill_session(self, session_id):
        reply = QMessageBox.question(
            self, "Kill Session",
            f"Kill session {session_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.parent, "kill_session"):
                self.parent.kill_session(session_id)

    def _ctx_run_module(self, module_path, session_id=None):
        try:
            fw = self.parent.framework
            if hasattr(fw, "cmd_use"):
                fw.cmd_use([module_path])
            if session_id and fw.loaded_module:
                for opt_name in ("SESSION", "SID", "SESSION_ID"):
                    try:
                        if hasattr(fw.loaded_module, "set_option"):
                            fw.loaded_module.set_option(opt_name, session_id)
                        break
                    except Exception:
                        pass
        except Exception as e:
            if hasattr(self.parent, "append_output"):
                self.parent.append_output(f"[red]Module load error: {e}[/]")

    def _ctx_copy_text(self, text):
        QApplication.clipboard().setText(str(text))

    def _ctx_reset_positions(self):
        self.custom_positions.clear()
        self.force_refresh()
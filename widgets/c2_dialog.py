# widgets/c2_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout,
    QMessageBox, QWidget, QTabWidget, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

import json
import threading
import socket

class C2ServerThread(QThread):
    output = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def __init__(self, host, port, web_port, password):
        super().__init__()
        self.host = host
        self.port = port
        self.web_port = web_port
        self.password = password
        self.server = None
        self.running = False
    
    def run(self):
        try:
            from modules.payload.c2_server import C2Server
            self.server = C2Server(self.host, self.port, self.web_port, self.password)
            self.running = True
            self.output.emit(f"[*] C2 Server started on {self.host}:{self.port}")
            self.output.emit(f"[*] Web panel: http://{self.host}:{self.web_port}")
            self.output.emit(f"[*] Password: {self.password}")
            self.output.emit("[*] Waiting for victims...")
            self.server.start()
        except Exception as e:
            self.output.emit(f"[!] Error: {e}")
            self.running = False
    
    def stop(self):
        if self.server:
            self.server.stop()
        self.running = False

class C2Dialog(QDialog):
    def __init__(self, framework=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.setWindowTitle("C2 Server")
        self.setModal(False)
        self.setMinimumSize(700, 600)
        
        self.server_thread = None
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("C2 SERVER")
        title.setStyleSheet("color: #00ff00; font-size: 18pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top: Form
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        form = QFormLayout()
        
        self.host_input = QLineEdit()
        self.host_input.setText("0.0.0.0")
        form.addRow("Listen Host:", self.host_input)
        
        self.port_input = QLineEdit()
        self.port_input.setText("4444")
        form.addRow("Listen Port:", self.port_input)
        
        self.web_port_input = QLineEdit()
        self.web_port_input.setText("5000")
        form.addRow("Web Panel Port:", self.web_port_input)
        
        self.password_input = QLineEdit()
        self.password_input.setText("admin")
        form.addRow("Panel Password:", self.password_input)
        
        form_layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start C2 Server")
        self.start_btn.clicked.connect(self._start_server)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop C2 Server")
        self.stop_btn.clicked.connect(self._stop_server)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        form_layout.addLayout(btn_layout)
        
        splitter.addWidget(form_widget)
        
        # Bottom: Output
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        output_label = QLabel("Console Output:")
        output_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        output_layout.addWidget(self.output_text)
        
        splitter.addWidget(output_widget)
        splitter.setSizes([250, 350])
        
        layout.addWidget(splitter)
    
    def _start_server(self):
        host = self.host_input.text()
        port = int(self.port_input.text())
        web_port = int(self.web_port_input.text())
        password = self.password_input.text()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.output_text.clear()
        
        self.server_thread = C2ServerThread(host, port, web_port, password)
        self.server_thread.output.connect(self._append_output)
        self.server_thread.start()
    
    def _stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._append_output("[*] C2 Server stopped")
    
    def _append_output(self, text):
        self.output_text.append(text)
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        self._stop_server()
        event.accept()
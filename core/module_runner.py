#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import signal
import threading
import sys
from contextlib import redirect_stdout, redirect_stderr
from PyQt6.QtCore import QThread, pyqtSignal, Qt


class PatchedPopen(subprocess.Popen):
    """Patched Popen untuk capture output ke GUI"""
    
    def __init__(self, *args, **kwargs):
        self.output_callback = kwargs.pop('output_callback', None)
        self._stop_reader = threading.Event()

        # Force capture output (text mode)
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.STDOUT)
        kwargs.setdefault('universal_newlines', True)
        kwargs.setdefault('bufsize', 1)

        # Ensure process group created for safe killing
        if os.name == 'posix':
            kwargs.setdefault('preexec_fn', os.setsid)
        else:
            kwargs.setdefault('creationflags', getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200))

        super().__init__(*args, **kwargs)

        # Spawn thread to read stdout
        if self.output_callback and self.stdout:
            self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self._reader_thread.daemon = True
            self._reader_thread.start()

    def stop_reader(self):
        """Stop the reader thread safely"""
        self._stop_reader.set()
        try:
            if self.stdout:
                self.stdout.close()
        except Exception:
            pass
        try:
            if self.stderr:
                self.stderr.close()
        except Exception:
            pass

    def _read_output(self):
        """Read output from subprocess and emit via callback"""
        try:
            while not self._stop_reader.is_set():
                try:
                    if self.stdout:
                        line = self.stdout.readline()
                        if not line:
                            break
                        try:
                            if self.output_callback:
                                self.output_callback(line.rstrip())
                        except Exception:
                            pass
                except ValueError:
                    break
                except Exception:
                    break
        except Exception:
            pass


class ModuleRunner(QThread):
    """
    Thread untuk menjalankan module dengan output capture.
    
    IMPROVEMENTS:
    - Properly stops ReverseTCPListener when interrupted
    - Registers listeners for cleanup
    - Uses non-blocking socket operations
    """
    
    output = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, framework, module_instance):
        super().__init__()
        self.framework = framework
        self.module_instance = module_instance

        # Capture object
        self.capture = None
        self.original_popen = subprocess.Popen
        self.original_system = os.system

        self._stop_flag = False
        self._active = []
        self._lock = threading.Lock()
        self._listeners = []  # track ReverseTCPListener instances

    def register_listener(self, listener):
        """
        Daftarkan listener agar bisa dihentikan saat stop()
        
        Args:
            listener: ReverseTCPListener instance yang akan dipantau
        """
        with self._lock:
            self._listeners.append(listener)
        
        self.output.emit(f"[cyan][*] Registered listener for cleanup[/]")

    def stop(self):
        """
        Request stop - non-blocking cleanup di background
        
        Properly stops:
        - ReverseTCPListener instances
        - Child subprocesses
        - Capture object
        """
        self._stop_flag = True
        self.output.emit("[yellow]Runner stop requested — terminating children...[/]")
        
        # Spawn background cleanup thread
        cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        cleanup_thread.start()

    def _background_cleanup(self):
        """Cleanup di background — tidak ngeblock GUI"""
        try:
            # === STOP REVERSE TCP LISTENERS ===
            # Stop semua ReverseTCPListener yang terdaftar
            with self._lock:
                listeners = list(self._listeners)

            for listener in listeners:
                try:
                    listener.running = False
                    
                    # Set stop event jika ada
                    if hasattr(listener, '_stop_event'):
                        listener._stop_event.set()
                    
                    # Give listener time to exit accept()
                    import time
                    time.sleep(0.2)
                    
                    # Shutdown socket
                    if hasattr(listener, 'server_socket') and listener.server_socket:
                        try:
                            import socket as _socket
                            listener.server_socket.shutdown(_socket.SHUT_RDWR)
                        except Exception:
                            pass
                        try:
                            listener.server_socket.close()
                            listener.server_socket = None
                        except Exception:
                            pass
                    
                    self.output.emit(f"[green][+] Stopped reverse_tcp listener[/]")
                    
                except Exception as e:
                    self.output.emit(f"[yellow][*] Listener cleanup error: {e}[/]")

            with self._lock:
                self._listeners.clear()

            # === KILL TRACKED SUBPROCESSES ===
            with self._lock:
                procs = list(self._active)
                for p in procs:
                    try:
                        if hasattr(p, 'stop_reader'):
                            p.stop_reader()
                    except Exception:
                        pass

            # Terminate dengan grace period
            for p in procs:
                try:
                    p.terminate()
                except Exception:
                    pass
            
            # Wait singkat
            import time
            try:
                for p in procs:
                    p.wait(timeout=0.2)
            except Exception:
                pass

            # Force kill jika masih hidup
            for p in procs:
                try:
                    if p.poll() is None:
                        if os.name == 'posix' and hasattr(os, "killpg"):
                            try:
                                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                            except Exception:
                                p.kill()
                        else:
                            p.kill()
                except Exception:
                    pass

            with self._lock:
                self._active.clear()

            # === STOP CAPTURE ===
            if self.capture:
                try:
                    self.capture.flush()
                except Exception:
                    pass
                    
        except Exception as e:
            self.output.emit(f"[red]Cleanup error: {e}[/]")

    def run(self):
        """
        Main thread execution
        
        FIXED:
        - Properly handles ReverseTCPListener
        - Registers listener with this runner for cleanup
        - Captures all output safely
        """
        from contextlib import redirect_stdout, redirect_stderr
        from core.capture import UniversalCapture
        
        # Create capture in the thread
        self.capture = UniversalCapture()
        self.capture.output_signal.connect(self.output.emit, Qt.ConnectionType.QueuedConnection)
        
        try:
            # Bind patched Popen & system
            subprocess.Popen = self._patched_popen
            os.system = self._patched_system

            # Run module with output capture
            try:
                with redirect_stdout(self.capture), redirect_stderr(self.capture):
                    if not self._stop_flag:
                        # Run module
                        result = self.module_instance.run(self.framework.session)
                        
                        # If module returns a string, emit it
                        if result and isinstance(result, str):
                            if result.strip():
                                self.output.emit(result)
                                
            except Exception as e:
                self.output.emit(f"[red]Module Error: {e}[/red]")
                import traceback
                self.output.emit(f"[red]{traceback.format_exc()}[/red]")

        except Exception as e:
            self.output.emit(f"[red]Runner fatal error: {e}[/red]")
            import traceback
            self.output.emit(f"[red]{traceback.format_exc()}[/red]")

        finally:
            # Restore globals
            try:
                subprocess.Popen = self.original_popen
            except Exception:
                pass
            try:
                os.system = self.original_system
            except Exception:
                pass

            # Cleanup leftover processes
            with self._lock:
                for p in self._active:
                    try:
                        if hasattr(p, 'stop_reader'):
                            p.stop_reader()
                    except Exception:
                        pass
                    try:
                        p.terminate()
                    except Exception:
                        pass
                    try:
                        p.wait(timeout=0.2)
                    except Exception:
                        pass
                self._active.clear()

            # Cleanup listeners
            with self._lock:
                for listener in self._listeners:
                    try:
                        listener.running = False
                        if hasattr(listener, '_stop_event'):
                            listener._stop_event.set()
                        if hasattr(listener, 'server_socket') and listener.server_socket:
                            try:
                                import socket as _socket
                                listener.server_socket.shutdown(_socket.SHUT_RDWR)
                            except:
                                pass
                            try:
                                listener.server_socket.close()
                            except:
                                pass
                    except Exception:
                        pass
                self._listeners.clear()

            # Stop capture
            try:
                if self.capture:
                    self.capture.flush()
            except Exception:
                pass

            # Notify GUI that we're finished
            self.finished.emit()

    def _patched_popen(self, *args, **kwargs):
        """Patched Popen with output callback"""
        kwargs['output_callback'] = self.output.emit

        try:
            p = PatchedPopen(*args, **kwargs)
        except TypeError:
            # Fallback to original Popen
            p = self.original_popen(*args, **kwargs)

        with self._lock:
            self._active.append(p)
        return p

    def _patched_system(self, cmd):
        """Patched os.system with output capture"""
        self.output.emit(f"$ {cmd}")
        p = self._patched_popen(cmd, shell=True)
        try:
            p.wait()
        except Exception:
            pass
        return getattr(p, "returncode", -1)

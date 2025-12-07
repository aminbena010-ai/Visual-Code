import sys
import time
import zipfile
import os
import requests
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QProgressBar, QLabel, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

# --- LIBRERÍA DE ACCESO DIRECTO (Para Windows) ---
try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    # Si winshell no está disponible (ej. Linux, macOS, o falta de instalación)
    print("Módulos 'winshell' o 'win32com' no encontrados. Los accesos directos solo se crearán en Windows.")
    winshell = None 
    Dispatch = None


# --- CLASE HILO DE TRABAJO ---
class WorkerThread(QThread):
    """
    Este hilo realiza la descarga, descompresión y configuración.
    """
    progress_updated = pyqtSignal(int)
    status_message = pyqtSignal(str)
    installation_finished = pyqtSignal(str)  # Emite la ruta del ejecutable principal
    installation_error = pyqtSignal(str)

    def __init__(self, github_url, temp_zip_path, destination_path, main_exec_name, parent=None):
        super().__init__(parent)
        self.github_url = github_url
        self.temp_zip_path = temp_zip_path
        self.destination_path = destination_path
        self.main_exec_name = main_exec_name
        self._is_running = True

    def run(self):
        if not self._is_running: return

        try:
            # --- 1. DESCARGA DEL ZIP DE GITHUB (0% - 20%) ---
            self.status_message.emit("Conectando con GitHub para descargar archivos...")
            self.progress_updated.emit(5)
            
            response = requests.get(self.github_url, stream=True, timeout=30) # Añadir timeout
            response.raise_for_status() # Lanza excepción para HTTP errors (4xx o 5xx)

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            self.status_message.emit("Descargando archivo ZIP...")
            
            with open(self.temp_zip_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    if not self._is_running: return
                    
                    file.write(data)
                    downloaded_size += len(data)
                    
                    # Progreso de descarga (0% a 20%)
                    if total_size > 0:
                        download_percent = int((downloaded_size / total_size) * 20)
                        self.progress_updated.emit(download_percent)

            # --- 2. DESCOMPRESIÓN Y COLOCACIÓN (20% - 90%) ---
            self.status_message.emit(f"Descarga completa. Descomprimiendo en {self.destination_path}...")
            self.progress_updated.emit(20)
            
            # Limpiar la carpeta de destino si existe (instalación limpia)
            if os.path.exists(self.destination_path):
                shutil.rmtree(self.destination_path)
            os.makedirs(self.destination_path)
            
            with zipfile.ZipFile(self.temp_zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                # Descompresión
                for i, file_name in enumerate(file_list):
                    if not self._is_running: return
                    
                    # Cálculo del progreso (del 20% al 90%)
                    progress_range = 90 - 20
                    decomp_percent = int((i / total_files) * progress_range) + 20
                    self.progress_updated.emit(decomp_percent)
                    self.status_message.emit(f"Descomprimiendo: {file_name}")
                    
                    time.sleep(0.01) # Simulación de tiempo
                    zip_ref.extract(file_name, self.destination_path)
            
            self.progress_updated.emit(90)

            # --- 3. CONFIGURACIÓN FINAL (90% - 100%) ---
            self.status_message.emit("Aplicando configuraciones adicionales y optimizaciones...")
            # Aquí puedes añadir tu lógica de configuración adicional (ej. ajustes de registro)
            time.sleep(2) 
            
            if not self._is_running: return

            # Rutas finales
            final_exec_path = os.path.join(self.destination_path, self.main_exec_name)
            
            # Finalizar
            self.progress_updated.emit(100)
            self.status_message.emit("¡Instalación completa!")
            self.installation_finished.emit(final_exec_path)

        except requests.exceptions.RequestException as e:
            self.installation_error.emit(f"Error de red o descarga. Verifica la URL: {e}")
        except FileNotFoundError:
            self.installation_error.emit("Error: No se puede acceder a la ruta de instalación.")
        except zipfile.BadZipFile:
            self.installation_error.emit("Error: Archivo ZIP inválido o corrupto.")
        except Exception as e:
            self.installation_error.emit(f"Ocurrió un error inesperado: {str(e)}")
        finally:
            if os.path.exists(self.temp_zip_path):
                try:
                    os.remove(self.temp_zip_path) # Limpiar el archivo ZIP temporal
                except OSError as e:
                    print(f"Advertencia: No se pudo eliminar el archivo temporal {self.temp_zip_path}: {e}")

    def stop(self):
        self._is_running = False
        self.wait()


# --- CLASE DE LA VENTANA PRINCIPAL (GUI) ---
class InstaladorApp(QMainWindow):
    """
    Ventana principal de la aplicación, configurada en modo oscuro y frameless.
    """
    def __init__(self):
        super().__init__()
        
        # === 1. CONFIGURACIÓN DE VENTANA SIN BORDES ===
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Instalador de Aplicación")
        self.setGeometry(100, 100, 550, 250)
        self.setFixedSize(self.size())
        
        # === 2. ESTILO DE MODO OSCURO (QSS) ===
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2e2e2e; /* Fondo oscuro */
                border: 1px solid #555555;
            }
            QLabel {
                color: #ffffff; /* Texto blanco */
                font-family: 'Segoe UI', Arial;
            }
            QLabel#titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #4CAF50; /* Título en color de acento */
            }
            QLabel#statusLabel {
                font-size: 14px;
                font-weight: bold;
                color: #cccccc;
            }
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                background-color: #3e3e3e;
            }
            QProgressBar::chunk {
                background-color: #4CAF50; /* Verde de progreso */
                border-radius: 6px;
            }
            QPushButton {
                background-color: #3e3e3e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)

        # Widget central y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 10, 20, 20)

        # === 3. BOTÓN DE CIERRE (CUSTOM) ===
        close_button = QPushButton("✕")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("QPushButton {background-color: #f44336; color: white; border: none; font-size: 14px;}")
        
        header_layout = QHBoxLayout()
        header_layout.addStretch(1)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        # Título
        self.title_label = QLabel("Asistente de Instalación")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Barra de Progreso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(20)
        layout.addWidget(self.progress_bar)

        # Etiqueta de Estado
        self.status_label = QLabel("Iniciando...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Botón de Estado/Log
        self.status_button = QPushButton("Instalación Iniciada Automáticamente")
        self.status_button.setEnabled(False)
        layout.addWidget(self.status_button)
        
        self.worker = None

        # --- CONFIGURACIONES ESPECÍFICAS ---
        self.ZIP_URL = "https://github.com/tu_usuario/tu_repositorio/archive/main.zip" # <-- ¡REEMPLAZAR POR LA URL RAW DE TU ZIP!
        self.APP_FOLDER_NAME = "MiProgramaInstalado"
        self.MAIN_EXECUTABLE = "programa.exe" # <-- REEMPLAZAR POR EL NOMBRE DE TU EJECUTABLE PRINCIPAL
        
        # === 4. EJECUCIÓN AUTOMÁTICA ===
        QTimer.singleShot(500, self.start_installation)
        

    def start_installation(self):
        """Prepara las rutas e inicia el proceso de instalación de forma automática."""
        
        # 1. Definir rutas en el Escritorio
        desktop_path = self.get_desktop_path()

        # Ruta final donde se instalará el programa (en el Escritorio)
        destination_path = os.path.join(desktop_path, self.APP_FOLDER_NAME)
        # Ruta temporal para guardar el zip descargado
        temp_zip_path = os.path.join(os.getcwd(), "downloaded_app.zip")
        
        self.status_button.setText("Instalando...")
        self.title_label.setText("Proceso de Instalación en Curso")

        # Crea y configura el hilo de trabajo
        self.worker = WorkerThread(
            self.ZIP_URL, 
            temp_zip_path, 
            destination_path, 
            self.MAIN_EXECUTABLE
        )
        
        # Conexión de señales
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_message.connect(self.status_label.setText)
        self.worker.installation_finished.connect(self.on_installation_finished)
        self.worker.installation_error.connect(self.on_installation_error)
        
        self.worker.start()

    def get_desktop_path(self):
        """Obtiene la ruta del Escritorio de forma compatible con múltiples OS."""
        if sys.platform == "win32" and winshell:
            # En Windows, usar winshell
            return winshell.desktop()
        else:
            # Para otros sistemas o si winshell falla, usar la carpeta de usuario/Desktop
            return os.path.join(os.path.expanduser('~'), 'Desktop')

    
    def create_shortcut(self, target_path):
        """Crea un acceso directo en el Escritorio (solo Windows)."""
        if sys.platform != "win32" or not winshell:
            return # No crear acceso directo en otros OS o sin librería
        
        try:
            desktop = winshell.desktop()
            shortcut_name = f"{self.APP_FOLDER_NAME}.lnk"
            path = os.path.join(desktop, shortcut_name)
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            
            shortcut.Targetpath = target_path
            shortcut.WorkingDirectory = os.path.dirname(target_path)
            
            # Opcional: Establecer un ícono si el ejecutable tiene uno
            # shortcut.IconLocation = target_path 
            
            shortcut.save()
            self.status_label.setText(f"Acceso directo creado: {shortcut_name}")
        except Exception as e:
            QMessageBox.warning(self, "Advertencia", f"No se pudo crear el acceso directo: {e}")
            self.status_label.setText(f"Advertencia: Error al crear acceso directo.")


    def on_installation_finished(self, final_exec_path):
        """Maneja el final de la instalación y crea el acceso directo."""
        self.status_button.setText("Instalación Completa")
        self.title_label.setText("Instalación Finalizada")
        self.progress_bar.setValue(100)
        self.status_label.setStyleSheet("color: #4CAF50;")
        
        # CREAR ACCESO DIRECTO
        self.status_label.setText("Creando acceso directo...")
        self.create_shortcut(final_exec_path)
        
        QMessageBox.information(self, "Completo", "La aplicación se ha instalado correctamente.")
        QTimer.singleShot(1000, self.close) # Cierre automático

    def on_installation_error(self, message):
        """Maneja los errores de instalación."""
        self.status_label.setText(f"ERROR: {message}")
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        self.status_button.setText("Error. Reinicia el programa para reintentar.")
        
        QMessageBox.critical(self, "Error de Instalación", message)
        self.worker = None

    # === MÉTODOS PARA MOVER LA VENTANA SIN BORDES ===
    def mousePressEvent(self, event):
        """Permite mover la ventana al presionar el botón izquierdo."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Mueve la ventana mientras se arrastra el mouse."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        """Asegura que el hilo se detenga si se cierra la ventana manualmente."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()

# --- PUNTO DE ENTRADA DE LA APLICACIÓN ---
if __name__ == "__main__":
    
    print("----------------------------------------------------------")
    print("INICIO DEL INSTALADOR")
    print("¡IMPORTANTE! Reemplaza 'self.ZIP_URL' y 'self.MAIN_EXECUTABLE' en el código.")
    print("----------------------------------------------------------")

    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))

    installer = InstaladorApp()
    installer.show()
    sys.exit(app.exec())
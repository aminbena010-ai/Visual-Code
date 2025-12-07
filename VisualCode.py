import os
import sys
import configparser
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QFileDialog, QStatusBar,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QToolBar, QDockWidget,
    QTreeView, QStackedWidget, QInputDialog, QTabWidget, QLineEdit,QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtGui import (
    QIcon, QAction, QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QFileSystemModel,
    QTextBlockFormat, QPalette, QPainter, QTextOption, QTextCursor, QKeySequence
)
from PyQt6.QtCore import QRegularExpression, QSize, Qt, QRect, QPoint

class NumerosDeLineaArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor_texto = editor
        # Establecer el color de fondo para que coincida con el tema oscuro
        self.setStyleSheet("background-color: #383A59;") 
        
    def sizeHint(self):
        """Devuelve el ancho preferido para esta barra lateral."""
        return QSize(self.editor_texto.ancho_area_numeros(), 0)

    def paintEvent(self, event):
        """Maneja el evento de dibujo (pintar los números de línea)."""
        self.editor_texto.dibujar_area_numeros(event)

# --- 1. Definición del Resaltador de Sintaxis ---

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.reglas_resaltado = []
        self.load_theme('lib/txt/txt.lib') # Cargar tema por defecto 'txt' al inicio

    def load_theme(self, theme_file):
        """Carga los colores desde un archivo de tema .lib y reconstruye las reglas."""
        # Colores por defecto en caso de que el archivo o una clave falte
        defaults = {
            'keyword': "#5151F0", 'operator': "#F79F34", 'string': "#F54141",
            'comment': "#2AC52A", 'function': "#D8AA37"
        }

        colors = defaults.copy()
        if os.path.exists(theme_file):
            parser = configparser.ConfigParser()
            parser.read(theme_file)
            if 'colors' in parser:
                for name, color_code in parser['colors'].items():
                    colors[name] = color_code

        # Paleta de Colores desde el archivo
        COLOR_KEYWORD = QColor(colors['keyword'])
        COLOR_OPERATOR = QColor(colors['operator'])
        COLOR_STRING = QColor(colors['string'])
        COLOR_COMMENT = QColor(colors['comment'])
        COLOR_FUNCTION = QColor(colors['function'])

        # Formatos
        self.formato_palabra_clave = self.crear_formato(COLOR_KEYWORD, 'bold')
        self.formato_operador = self.crear_formato(COLOR_OPERATOR)
        self.formato_cadena = self.crear_formato(COLOR_STRING)
        self.formato_comentario = self.crear_formato(COLOR_COMMENT, 'italic')
        self.formato_funcion = self.crear_formato(COLOR_FUNCTION)
        
        # Limpiar reglas antiguas y definir las nuevas con los formatos actualizados
        self.reglas_resaltado = []
        self.definir_reglas()
        self.rehighlight() # Forzar el repintado de todo el documento

    def crear_formato(self, color, estilo=None):
        formato = QTextCharFormat()
        formato.setForeground(color)
        if estilo == 'bold':
            formato.setFontWeight(QFont.Weight.Bold)
        elif estilo == 'italic':
            formato.setFontItalic(True)
        return formato

    def definir_reglas(self):
        palabras_clave = ['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield']
        for palabra in palabras_clave:
            patron = r'\b' + palabra + r'\b'
            self.reglas_resaltado.append((QRegularExpression(patron), self.formato_palabra_clave))

        operadores = [r'=', r'\+', r'-', r'\*', r'/', r'%', r'!', r'==', r'!=', r'&gt;', r'&lt;', r'&gt;=', r'&lt;=', r'\(', r'\)', r'\[', r'\]', r'\{', r'\}', r',']
        for operador in operadores:
            self.reglas_resaltado.append((QRegularExpression(operador), self.formato_operador))

        self.reglas_resaltado.append((QRegularExpression(r"'[^']*'"), self.formato_cadena))
        self.reglas_resaltado.append((QRegularExpression(r'"[^\"]*"'), self.formato_cadena))
        self.reglas_resaltado.append((QRegularExpression(r'#.*'), self.formato_comentario))
        self.reglas_resaltado.append((QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), self.formato_funcion))
        
    def highlightBlock(self, texto):
        for patron_expr, formato in self.reglas_resaltado:
            iterator = patron_expr.globalMatch(texto)
            while iterator.hasNext():
                match = iterator.next()
                inicio = match.capturedStart()
                longitud = match.capturedLength()
                self.setFormat(inicio, longitud, formato)

# --- NUEVA CLASE ---

class EditorConNumeros(QWidget):
    """Contenedor que une QPlainTextEdit con NumerosDeLineaArea."""
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window # Referencia a VentanaPrincipal
        
        self.ruta_archivo = None # Ruta específica para este editor
        self.es_guardado = True # Estado de guardado del archivo
        
        # El widget de texto real
        self.text_editor = QPlainTextEdit()
        
        # 🟢 IMPLEMENTACIÓN DE TEMA Y TIPOGRAFÍA (Movido desde la ventana principal)
        COLOR_FONDO = QColor("#282A36")
        COLOR_TEXTO = QColor("#F8F8F2")
        paleta = self.text_editor.palette()
        paleta.setColor(QPalette.ColorRole.Base, COLOR_FONDO)
        paleta.setColor(QPalette.ColorRole.Text, COLOR_TEXTO)
        self.text_editor.setPalette(paleta)
        
        font = QFont("Cascadia Code")
        font.setPointSize(11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_editor.setFont(font)
        
        # Ajuste de altura de línea
        cursor = self.text_editor.textCursor()
        block_format = cursor.blockFormat()
        block_format.setLineHeight(1.3, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cursor.select(cursor.SelectionType.Document)
        cursor.mergeBlockFormat(block_format)
        cursor.clearSelection()
        self.text_editor.setTextCursor(cursor)
        
        self.text_editor.setWordWrapMode(QTextOption.WrapMode.NoWrap) # Sin ajuste por defecto

        # Área de Números de Línea
        self.area_numeros = NumerosDeLineaArea(self) # Pasa la instancia de este contenedor
        
        # Layout para el editor y los números
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.area_numeros)
        layout.addWidget(self.text_editor)

        # Resaltador
        self.highlighter = PythonHighlighter(self.text_editor.document())

        # Conexiones específicas de este editor
        self.text_editor.document().blockCountChanged.connect(self.actualizar_ancho_area_numeros)
        self.text_editor.updateRequest.connect(self.actualizar_area_numeros_update)
        self.text_editor.textChanged.connect(self.marcar_no_guardado)
        self.text_editor.cursorPositionChanged.connect(self.parent_window.actualizar_barra_estado)
        
        self.actualizar_ancho_area_numeros()
        
    # --- MÉTODOS DE NÚMEROS DE LÍNEA (Movidos desde la ventana principal) ---
    def ancho_area_numeros(self):
        """Calcula el ancho necesario basado en el número máximo de líneas."""
        digitos = max(1, len(str(self.text_editor.document().blockCount())))
        ancho = 10 + self.text_editor.fontMetrics().horizontalAdvance('9') * digitos
        return ancho

    def actualizar_ancho_area_numeros(self):
        """Informa al layout que el ancho de la barra de números ha cambiado."""
        self.area_numeros.updateGeometry()

    def actualizar_area_numeros_update(self, rect, dy):
        """Maneja el scroll y repinta el área de números."""
        if dy:
            self.area_numeros.scroll(0, dy) # Mueve el widget de números
        else:
            # Repinta el área visible cuando hay otros cambios (ej. selección)
            self.area_numeros.update(0, rect.y(), self.area_numeros.width(), rect.height())

    def dibujar_area_numeros(self, event):
        """El método de dibujo real para los números de línea."""
        painter = QPainter(self.area_numeros)
        painter.fillRect(event.rect(), QColor("#383A59"))
        
        bloque = self.text_editor.firstVisibleBlock()
        numero_linea = bloque.blockNumber()
        pos_y_inicial = self.text_editor.blockBoundingGeometry(bloque).translated(self.text_editor.contentOffset()).top()
        top = int(pos_y_inicial)

        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        
        COLOR_LINEA = QColor("#6272A4")
        painter.setPen(COLOR_LINEA)
        
        while bloque.isValid() and top <= event.rect().bottom():
            altura_bloque = int(self.text_editor.blockBoundingRect(bloque).height())

            if bloque.isVisible() and top >= event.rect().top():
                ancho = self.ancho_area_numeros() - 5
                rect = QRect(0, top, ancho, altura_bloque)
                painter.drawText(rect, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), str(numero_linea + 1))
            
            top += altura_bloque
            bloque = bloque.next()
            numero_linea += 1
            
    # --- MÉTODOS DE ESTADO ---
    def marcar_no_guardado(self):
        if self.es_guardado:
            self.es_guardado = False
            self.parent_window.actualizar_titulo_pestana(self)
            self.parent_window.actualizar_contador_caracteres()
            
    def marcar_guardado(self):
        self.es_guardado = True
        self.parent_window.actualizar_titulo_pestana(self)

class VentanaPrincipal(QMainWindow):
    # 🟢 NUEVO: Clase interna para manejar la barra de título y el arrastre
    class BarraDeTitulo(QMenuBar):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent_window = parent
            self.drag_pos = None

        def mousePressEvent(self, event):
            # Si el clic es sobre una acción de menú (Archivo, Editar, etc.), dejar que se maneje normalmente.
            if self.actionAt(event.pos()):
                super().mousePressEvent(event)
            # Si no, tratarlo como un inicio de arrastre de ventana.
            elif event.button() == Qt.MouseButton.LeftButton:
                self.parent_window.drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event):
            if self.parent_window.drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
                self.parent_window.move(event.globalPosition().toPoint() - self.parent_window.drag_pos)
                event.accept()
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            self.parent_window.drag_pos = None
            super().mouseReleaseEvent(event)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mi Editor de Texto PyQt6")
        self.resize(1000, 700) # Tamaño inicial por defecto
        self.ruta_actual = None
        
        # --- Configuración de ventana sin marco ---
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.drag_pos = None # Movido a la barra de título, pero mantenemos la referencia aquí

        self.cargar_configuracion_temas()

        # --- Panel de botones izquierdo ---
        self.barra_actividades = QToolBar("Barra de Actividades")
        self.barra_actividades.setMovable(False)
        self.barra_actividades.setFloatable(False)
        self.barra_actividades.setFixedWidth(50)
        self.barra_actividades.setStyleSheet("QToolBar { background-color: #21222C; border: none; }")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.barra_actividades)

        # Widget contenedor para los botones dentro de la QToolBar
        widget_botones = QWidget()
        layout_botones = QVBoxLayout(widget_botones)
        layout_botones.setContentsMargins(5, 10, 5, 10) # Margen superior e inferior
        layout_botones.setSpacing(15) # Espacio entre botones
        layout_botones.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinear botones en la parte superior

        # Crear 4 botones de ejemplo
        self.boton_explorador = QPushButton("E")
        self.boton_buscar = QPushButton("B")
        self.boton_git = QPushButton("G")
        self.boton_ajustes = QPushButton("A")

        # Tooltips para los botones
        self.boton_explorador.setToolTip("Explorador de archivos")
        self.boton_buscar.setToolTip("Buscar en el archivo")
        self.boton_git.setToolTip("Control de versiones")
        self.boton_ajustes.setToolTip("Ajustes")

        # Estilo para los botones del panel
        estilo_boton_panel = """
            QPushButton {
                color: #BD93F9;
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #F8F8F2;
            }
        """
        for boton in [self.boton_explorador, self.boton_buscar, self.boton_git, self.boton_ajustes]:
            boton.setStyleSheet(estilo_boton_panel)
            layout_botones.addWidget(boton)
        
        self.barra_actividades.addWidget(widget_botones)

        # --- Panel del Explorador de Archivos (Dock Widget) ---
        self.dock_explorador = QDockWidget("Explorador", self)
        self.dock_explorador.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.dock_explorador.setStyleSheet("QDockWidget { background-color: #282A36; color: #F8F8F2; }")
        
        # Contenedor principal para el DockWidget
        explorador_container = QWidget()
        layout_principal_explorador = QVBoxLayout(explorador_container)
        layout_principal_explorador.setContentsMargins(0, 5, 0, 0)
        layout_principal_explorador.setSpacing(5)

        # --- Cabecera con botones de acción (Nuevo Archivo/Carpeta) ---
        self.cabecera_explorador = QWidget()
        layout_cabecera = QHBoxLayout(self.cabecera_explorador)
        layout_cabecera.setContentsMargins(5, 0, 5, 0)
        self.boton_nuevo_archivo = QPushButton("📄 Archivo")
        self.boton_nueva_carpeta = QPushButton("📁 Carpeta")
        layout_cabecera.addWidget(self.boton_nuevo_archivo)
        layout_cabecera.addWidget(self.boton_nueva_carpeta)
        self.cabecera_explorador.hide() # Oculta por defecto

        # --- Vista de Bienvenida (cuando no hay carpeta abierta) ---
        self.vista_bienvenida = QWidget()
        layout_bienvenida = QVBoxLayout(self.vista_bienvenida)
        layout_bienvenida.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_bienvenida.setSpacing(15)
        
        self.boton_abrir_carpeta = QPushButton("📂 Abrir Carpeta")
        self.boton_abrir_archivo_explorador = QPushButton("📄 Abrir Archivo")
        
        estilo_botones_bienvenida = """
            QPushButton { 
                background-color: #44475A; color: #F8F8F2; 
                border: 1px solid #6272A4; padding: 8px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #6272A4; }
        """
        self.boton_abrir_carpeta.setStyleSheet(estilo_botones_bienvenida)
        self.boton_abrir_archivo_explorador.setStyleSheet(estilo_botones_bienvenida)

        layout_bienvenida.addWidget(self.boton_abrir_carpeta)
        layout_bienvenida.addWidget(self.boton_abrir_archivo_explorador)

        # --- Vista del Árbol de Archivos ---
        self.model = QFileSystemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setAnimated(True) # Pequeña animación al expandir/colapsar
        self.tree_view.setIndentation(15) # Indentación para los elementos
        self.tree_view.setSortingEnabled(True)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)

        # --- StackedWidget para cambiar entre bienvenida y árbol ---
        self.stacked_widget_explorador = QStackedWidget()
        self.stacked_widget_explorador.addWidget(self.vista_bienvenida)
        self.stacked_widget_explorador.addWidget(self.tree_view)

        # Añadir widgets al layout principal del explorador
        layout_principal_explorador.addWidget(self.cabecera_explorador)
        layout_principal_explorador.addWidget(self.stacked_widget_explorador)

        self.dock_explorador.setWidget(explorador_container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_explorador)
        self.dock_explorador.hide() # Oculto por defecto

        # Conectar el botón para mostrar/ocultar el panel
        self.boton_explorador.clicked.connect(self.alternar_panel_explorador)
        
        # Conectar botones de la vista de bienvenida
        self.boton_abrir_carpeta.clicked.connect(self.abrir_carpeta_en_explorador)
        self.boton_abrir_archivo_explorador.clicked.connect(self.abrir_archivo_y_carpeta_en_explorador)

        # Conectar doble clic en el árbol para abrir archivos
        self.tree_view.doubleClicked.connect(self.abrir_archivo_desde_explorador)

        # Conectar botones de creación
        self.boton_nuevo_archivo.clicked.connect(self.crear_nuevo_archivo)
        self.boton_nueva_carpeta.clicked.connect(self.crear_nueva_carpeta)

        # 🟢 NUEVO: QTabWidget como widget central
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True) # Permitir cerrar pestañas
        self.tab_widget.setDocumentMode(True) # Estilo moderno, similar a VS Code
        self.tab_widget.tabCloseRequested.connect(self.cerrar_pestana) # Conectar la señal de cierre
        self.tab_widget.currentChanged.connect(self.actualizar_estado_completo)

        # Estilo para las pestañas (Dracula)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { 
                background-color: #44475A; 
                color: #F8F8F2; 
                padding: 5px 15px;
                margin-right: 1px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected { 
                background-color: #282A36; /* Mismo color que el fondo del editor */
                border-bottom: 2px solid #50FA7B; /* Línea verde de foco */
            }
            QTabBar::tab:!selected:hover {
                background-color: #6272A4;
            }
            QTabBar::close-button {
                image: url(lib/icons/close.png); /* Asegúrate de tener un ícono de cierre */
                subcontrol-position: right;
            }
            QTabBar::close-button:hover {
                background: #FF5555;
            }
        """)

        self.setCentralWidget(self.tab_widget)

        # Asegurar que la ventana principal también tenga un fondo oscuro
        self.setStyleSheet("QMainWindow { background-color: #282A36; }")

        # --- ACCIONES Y MENÚS ---
        self.crear_acciones()
        self.crear_acciones_editor() # Añadiremos la acción de wrap aquí
        self.crear_barra_menu()
        self.crear_barra_estado()

        # 🟢 NUEVO: Barra de Búsqueda/Reemplazo (como superposición)
        self.widget_busqueda = self.crear_widget_busqueda()
        self.widget_busqueda.hide()

        self.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.widget_busqueda.isVisible():
            # Vuelve a llamar a mostrar_barra_busqueda para recalcular la posición
            self.mostrar_barra_busqueda(modo_reemplazar=(hasattr(self, '_reemplazo_widgets') and self._reemplazo_widgets))

    # --- MÉTODOS DE GESTIÓN DE PESTAÑAS ---
    def obtener_editor_activo(self):
        """Devuelve la instancia actual de EditorConNumeros en la pestaña activa."""
        return self.tab_widget.currentWidget()

    def actualizar_titulo_pestana(self, editor):
        """Actualiza el título de la pestaña para mostrar si está modificado (*)."""
        index = self.tab_widget.indexOf(editor)
        if index != -1:
            nombre_base = os.path.basename(editor.ruta_archivo) if editor.ruta_archivo else "Sin título"
            titulo = f"{nombre_base}{' *' if not editor.es_guardado else ''}"
            self.tab_widget.setTabText(index, titulo)

    def cerrar_pestana(self, index):
        """Maneja el cierre de una pestaña, pidiendo guardar si está modificado."""
        editor_a_cerrar = self.tab_widget.widget(index)

        if editor_a_cerrar and not editor_a_cerrar.es_guardado:
            # Aquí se podría implementar un diálogo de confirmación.
            # Por simplicidad, solo notificaremos y cancelaremos el cierre.
            self.barra_estado.showMessage("Advertencia: Archivo modificado. ¡Guarda antes de cerrar!", 5000)
            return

        self.tab_widget.removeTab(index)
        editor_a_cerrar.deleteLater()

    # --- MÉTODOS DE ARCHIVO ---
    
    def abrir_archivo(self):
        ruta_archivo, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo", "", "Archivos de texto (*.txt);;Todos los archivos (*)")
        if ruta_archivo:
            # Verificar si el archivo ya está abierto
            for i in range(self.tab_widget.count()):
                editor_existente = self.tab_widget.widget(i)
                if editor_existente.ruta_archivo == ruta_archivo:
                    self.tab_widget.setCurrentIndex(i)
                    self.barra_estado.showMessage(f"Archivo ya abierto en la pestaña {i+1}", 3000)
                    return
            
            try:
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                nuevo_editor_widget = EditorConNumeros(self)
                nuevo_editor_widget.text_editor.setPlainText(contenido)
                nuevo_editor_widget.ruta_archivo = ruta_archivo
                nuevo_editor_widget.marcar_guardado()

                index = self.tab_widget.addTab(nuevo_editor_widget, os.path.basename(ruta_archivo))
                self.tab_widget.setCurrentIndex(index)
                
                self.actualizar_info_lenguaje()
                self.actualizar_barra_estado()

            except Exception as e:
                print(f"Error al abrir el archivo: {e}")

    def guardar_archivo(self):
        editor = self.obtener_editor_activo()
        if not editor: return

        if editor.ruta_archivo:
            try:
                with open(editor.ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(editor.text_editor.toPlainText())
                editor.marcar_guardado()
                self.barra_estado.showMessage(f"Archivo guardado: {os.path.basename(editor.ruta_archivo)}", 3000)
            except Exception as e:
                print(f"Error al guardar el archivo: {e}")
        else:
            self.guardar_como()

    def guardar_como(self):
        editor = self.obtener_editor_activo()
        if not editor: return

        ruta_archivo, _ = QFileDialog.getSaveFileName(self, "Guardar Archivo", "", "Archivos de texto (*.txt);;Todos los archivos (*)")
        if ruta_archivo:
            try:
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(editor.text_editor.toPlainText())
                editor.ruta_archivo = ruta_archivo
                editor.marcar_guardado()
                self.actualizar_titulo_pestana(editor)
                self.actualizar_info_lenguaje()
                self.barra_estado.showMessage(f"Archivo guardado en: {os.path.basename(ruta_archivo)}", 3000)
            except Exception as e:
                print(f"Error al guardar el archivo: {e}")
                
    def abrir_archivo_desde_explorador(self, index):
        """Abre un archivo al hacer doble clic en el QTreeView."""
        ruta_archivo = self.model.filePath(index)
        # Asegurarse de que no es un directorio
        if not self.model.isDir(index):
            # Reutilizamos la lógica de abrir_archivo, pero pasándole la ruta
            self.abrir_archivo_con_ruta(ruta_archivo)
    
    def abrir_carpeta_en_explorador(self):
        """Abre un diálogo para seleccionar una carpeta y la muestra en el QTreeView."""
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if directorio:
            self.model.setRootPath(directorio)
            self.tree_view.setRootIndex(self.model.index(directorio))
            self.stacked_widget_explorador.setCurrentWidget(self.tree_view)
            self.cabecera_explorador.show()
            self.dock_explorador.setWindowTitle(f"Explorador - {os.path.basename(directorio)}")

    def abrir_archivo_y_carpeta_en_explorador(self):
        """Abre un archivo y carga su carpeta contenedora en el explorador."""
        ruta_archivo, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo")
        if ruta_archivo:
            self.abrir_archivo_con_ruta(ruta_archivo)
            # Cargar la carpeta contenedora en el explorador
            directorio = os.path.dirname(ruta_archivo)
            self.model.setRootPath(directorio)
            self.tree_view.setRootIndex(self.model.index(directorio))
            self.stacked_widget_explorador.setCurrentWidget(self.tree_view)
            self.cabecera_explorador.show()
            self.dock_explorador.setWindowTitle(f"Explorador - {os.path.basename(directorio)}")

    def abrir_archivo_con_ruta(self, ruta_archivo):
        """Función auxiliar para abrir un archivo desde una ruta dada (usada por explorador)."""
        for i in range(self.tab_widget.count()):
            editor_existente = self.tab_widget.widget(i)
            if editor_existente.ruta_archivo == ruta_archivo:
                self.tab_widget.setCurrentIndex(i)
                return
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            nuevo_editor = EditorConNumeros(self)
            nuevo_editor.text_editor.setPlainText(contenido)
            nuevo_editor.ruta_archivo = ruta_archivo
            nuevo_editor.marcar_guardado()
            index = self.tab_widget.addTab(nuevo_editor, os.path.basename(ruta_archivo))
            self.tab_widget.setCurrentWidget(nuevo_editor)
            self.actualizar_estado_completo()
        except Exception as e:
            print(f"Error al abrir archivo desde explorador: {e}")

    def crear_nuevo_archivo(self):
        """Crea un nuevo archivo en el directorio seleccionado o en la raíz."""
        indices = self.tree_view.selectedIndexes()
        ruta_base = self.model.rootPath()
        if indices:
            ruta_seleccionada = self.model.filePath(indices[0])
            if self.model.isDir(indices[0]):
                ruta_base = ruta_seleccionada
            else:
                ruta_base = os.path.dirname(ruta_seleccionada)

        nombre_archivo, ok = QInputDialog.getText(self, "Nuevo Archivo", "Introduce el nombre del archivo:")
        if ok and nombre_archivo:
            ruta_completa = os.path.join(ruta_base, nombre_archivo)
            if not os.path.exists(ruta_completa):
                open(ruta_completa, 'a').close() # Crea el archivo vacío
            else:
                self.barra_estado.showMessage("Error: El archivo ya existe.", 3000)

    def crear_nueva_carpeta(self):
        """Crea una nueva carpeta en el directorio seleccionado o en la raíz."""
        indices = self.tree_view.selectedIndexes()
        ruta_base = self.model.rootPath()
        if indices:
            ruta_seleccionada = self.model.filePath(indices[0])
            if self.model.isDir(indices[0]):
                ruta_base = ruta_seleccionada
            else:
                ruta_base = os.path.dirname(ruta_seleccionada)
        
        nombre_carpeta, ok = QInputDialog.getText(self, "Nueva Carpeta", "Introduce el nombre de la carpeta:")
        if ok and nombre_carpeta:
            os.makedirs(os.path.join(ruta_base, nombre_carpeta), exist_ok=True)
            
    def cargar_configuracion_temas(self):
        """Carga la configuración de temas desde el archivo JSON."""
        self.theme_config = {}
        try:
            with open('lib/themes.json', 'r', encoding='utf-8') as f:
                self.theme_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Advertencia: No se pudo cargar 'lib/themes.json'. Se usarán valores por defecto. Error: {e}")

    # --- MÉTODOS DE BÚSQUEDA Y REEMPLAZO ---

    def crear_widget_busqueda(self):
        """Crea y configura el widget de búsqueda y reemplazo estilo VS Code."""
        busqueda_container = QWidget(self)
        busqueda_container.setStyleSheet("background-color: #44475A; border: 1px solid #6272A4; border-radius: 4px; padding: 5px;")

        layout = QHBoxLayout(busqueda_container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.campo_buscar = QLineEdit()
        self.campo_buscar.setPlaceholderText("Buscar (Ctrl+F)")
        self.campo_buscar.setStyleSheet("QLineEdit { background-color: #282A36; color: #F8F8F2; border: 1px solid #6272A4; padding: 3px; }")
        self.campo_buscar.returnPressed.connect(self.buscar_siguiente)

        self.campo_reemplazar = QLineEdit()
        self.campo_reemplazar.setPlaceholderText("Reemplazar (Ctrl+H)")
        self.campo_reemplazar.setStyleSheet("QLineEdit { background-color: #282A36; color: #F8F8F2; border: 1px solid #6272A4; padding: 3px; }")

        self.boton_match_case = QPushButton("Aa")
        self.boton_match_case.setCheckable(True)
        self.boton_match_case.setToolTip("Coincidir mayúsculas/minúsculas (Case Sensitive)")

        self.boton_regex = QPushButton(".*")
        self.boton_regex.setCheckable(True)
        self.boton_regex.setToolTip("Usar Expresiones Regulares (Regex)")

        self.boton_palabra_completa = QPushButton("W")
        self.boton_palabra_completa.setCheckable(True)
        self.boton_palabra_completa.setToolTip("Palabra completa")

        self.boton_anterior = QPushButton("▲")
        self.boton_anterior.setToolTip("Anterior (Shift+F3)")
        self.boton_anterior.clicked.connect(self.buscar_anterior)

        self.boton_siguiente = QPushButton("▼")
        self.boton_siguiente.setToolTip("Siguiente (F3)")
        self.boton_siguiente.clicked.connect(self.buscar_siguiente)

        self.boton_reemplazar_uno = QPushButton("Reemplazar")
        self.boton_reemplazar_uno.clicked.connect(self.reemplazar_uno)

        self.boton_reemplazar_todo = QPushButton("Todo")
        self.boton_reemplazar_todo.clicked.connect(self.reemplazar_todo)

        self.boton_cerrar = QPushButton("X")
        self.boton_cerrar.setToolTip("Cerrar (Escape)")
        self.boton_cerrar.clicked.connect(self.ocultar_barra_busqueda)

        layout.addWidget(self.campo_buscar)
        layout.addWidget(self.boton_match_case)
        layout.addWidget(self.boton_regex)
        layout.addWidget(self.boton_palabra_completa)
        layout.addWidget(self.boton_anterior)
        layout.addWidget(self.boton_siguiente)
        layout.addWidget(self.boton_cerrar)

        busqueda_container.setLayout(layout)
        busqueda_container.adjustSize()
        return busqueda_container

    def mostrar_barra_busqueda(self, modo_reemplazar=False):
        editor = self.obtener_editor_activo()
        if editor is None: return

        self._configurar_modo_busqueda(modo_reemplazar)

        ancho_ventana = self.width()
        ancho_widget = self.widget_busqueda.sizeHint().width()
        posicion_x = ancho_ventana - ancho_widget - 10
        posicion_y = self.menuBar().height() + 5

        self.widget_busqueda.move(posicion_x, posicion_y)
        self.widget_busqueda.show()
        self.campo_buscar.setFocus()
        self.boton_buscar.setChecked(True)

    def ocultar_barra_busqueda(self):
        self.widget_busqueda.hide()
        editor = self.obtener_editor_activo()
        if editor:
            editor.text_editor.setFocus()
        self.boton_buscar.setChecked(False)

    def _configurar_modo_busqueda(self, modo_reemplazar):
        layout = self.widget_busqueda.layout()

        if hasattr(self, '_reemplazo_widgets') and self._reemplazo_widgets:
            for widget in self._reemplazo_widgets:
                layout.removeWidget(widget)
                widget.hide()
            self._reemplazo_widgets = []

        if modo_reemplazar:
            self._reemplazo_widgets = [
                self.campo_reemplazar,
                self.boton_reemplazar_uno,
                self.boton_reemplazar_todo
            ]
            index = layout.indexOf(self.boton_anterior)
            layout.insertWidget(index, self.campo_reemplazar)
            layout.insertWidget(index + 1, self.boton_reemplazar_uno)
            layout.insertWidget(index + 2, self.boton_reemplazar_todo)
            for widget in self._reemplazo_widgets:
                widget.show()
        
        self.widget_busqueda.adjustSize()

    def mostrar_u_ocultar_busqueda(self):
        if self.widget_busqueda.isVisible():
            self.ocultar_barra_busqueda()
        else:
            self.mostrar_barra_busqueda()

    def get_opciones_busqueda(self):
        opciones = QTextDocument.FindFlag(0)
        if self.boton_match_case.isChecked():
            opciones |= QTextDocument.FindFlag.FindCaseSensitively
        if self.boton_palabra_completa.isChecked():
            opciones |= QTextDocument.FindFlag.FindWholeWords
        return opciones

    def buscar_siguiente(self):
        editor = self.obtener_editor_activo()
        if not editor: return
        texto_a_buscar = self.campo_buscar.text()
        if not texto_a_buscar: return
        
        opciones = self.get_opciones_busqueda()
        
        # Determinar si buscar con Regex o texto plano
        if self.boton_regex.isChecked():
            patron = QRegularExpression(texto_a_buscar)
            encontrado = editor.text_editor.find(patron, opciones)
        else:
            encontrado = editor.text_editor.find(texto_a_buscar, opciones)

        if not encontrado:
            editor.text_editor.moveCursor(QTextCursor.MoveOperation.Start)
            # Reintentar la búsqueda desde el principio
            if self.boton_regex.isChecked():
                editor.text_editor.find(QRegularExpression(texto_a_buscar), opciones)
            else:
                editor.text_editor.find(texto_a_buscar, opciones)

    def buscar_anterior(self):
        editor = self.obtener_editor_activo()
        if not editor: return
        texto_a_buscar = self.campo_buscar.text()
        if not texto_a_buscar: return

        opciones = self.get_opciones_busqueda() | QTextDocument.FindFlag.FindBackward
        
        # Determinar si buscar con Regex o texto plano
        if self.boton_regex.isChecked():
            patron = QRegularExpression(texto_a_buscar)
            encontrado = editor.text_editor.find(patron, opciones)
        else:
            encontrado = editor.text_editor.find(texto_a_buscar, opciones)

        if not encontrado:
            editor.text_editor.moveCursor(QTextCursor.MoveOperation.End)
            # Reintentar la búsqueda desde el final
            if self.boton_regex.isChecked():
                editor.text_editor.find(QRegularExpression(texto_a_buscar), opciones)
            else:
                editor.text_editor.find(texto_a_buscar, opciones)

    def reemplazar_uno(self):
        editor = self.obtener_editor_activo()
        if not editor: return

        cursor = editor.text_editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.campo_reemplazar.text())
        self.buscar_siguiente()

    def reemplazar_todo(self):
        editor = self.obtener_editor_activo()
        if not editor: return
        texto_a_buscar = self.campo_buscar.text()
        if not texto_a_buscar: return
        texto_reemplazo = self.campo_reemplazar.text()
        opciones = self.get_opciones_busqueda()
        
        documento = editor.text_editor.document()
        cursor = QTextCursor(documento)
        documento.undoStack().beginMacro("Reemplazar todo")

        contador = 0
        while True:
            # Usar QRegularExpression si el botón está activado
            if self.boton_regex.isChecked():
                cursor = documento.find(QRegularExpression(texto_a_buscar), cursor, opciones)
            else:
                cursor = documento.find(texto_a_buscar, cursor, opciones)

            if cursor.isNull():
                break
            cursor.insertText(texto_reemplazo)
            contador += 1
        documento.undoStack().endMacro()
        
        if contador > 0:
            self.barra_estado.showMessage(f"Reemplazados {contador} elementos.", 3000)
        else:
            self.barra_estado.showMessage("No se encontraron coincidencias.", 3000)

    # --- GESTIÓN DE CURSOR/ESTADO ---
    def actualizar_barra_estado(self):
        editor = self.obtener_editor_activo()
        if not editor:
            self.label_posicion_cursor.setText("Línea: --, Col: --")
            return
        cursor = editor.text_editor.textCursor()
        linea = cursor.blockNumber() + 1
        columna = cursor.columnNumber() + 1
        self.label_posicion_cursor.setText(f"Línea: {linea}, Col: {columna}")

    def actualizar_contador_caracteres(self):
        editor = self.obtener_editor_activo()
        if not editor:
            self.label_contador_caracteres.setText("Caracteres: 0")
            return
        num_caracteres = len(editor.text_editor.toPlainText())
        self.label_contador_caracteres.setText(f"Caracteres: {num_caracteres}")

    def actualizar_info_lenguaje(self):
        editor = self.obtener_editor_activo()
        if not editor or not editor.ruta_archivo:
            self.label_lenguaje.setText(self.theme_config.get('default_name', 'Texto Plano'))
            if editor:
                editor.highlighter.load_theme(self.theme_config.get('default_theme', 'lib/txt/txt.lib'))
            return

        _, ext = os.path.splitext(editor.ruta_archivo)
        ext = ext.lower()
        lang_config = self.theme_config.get('languages', {}).get(ext)

        if lang_config:
            self.label_lenguaje.setText(lang_config.get('name', 'Desconocido'))
            editor.highlighter.load_theme(lang_config.get('theme'))
        else:
            self.label_lenguaje.setText(self.theme_config.get('default_name', 'Texto Plano'))
            editor.highlighter.load_theme(self.theme_config.get('default_theme', 'lib/txt/txt.lib'))
    
    def actualizar_estado_completo(self):
        self.actualizar_barra_estado()
        self.actualizar_contador_caracteres()
        self.actualizar_info_lenguaje()

    # --- MÉTODOS DE BARRAS/ACCIONES ---

    def crear_acciones_editor(self):
        # 📝 Menú Editar (Conectado a las funciones nativas de QTextEdit)
        
        # 🟢 NUEVOS ATAJOS BÁSICOS
        self.accion_deshacer = QAction("&Deshacer", self)
        self.accion_deshacer.setShortcut("Ctrl+Z")
        self.accion_deshacer.triggered.connect(lambda: self.obtener_editor_activo().text_editor.undo() if self.obtener_editor_activo() else None)

        self.accion_rehacer = QAction("&Rehacer", self)
        self.accion_rehacer.setShortcut("Ctrl+Y")
        self.accion_rehacer.triggered.connect(lambda: self.obtener_editor_activo().text_editor.redo() if self.obtener_editor_activo() else None)

        self.accion_cortar = QAction("&Cortar", self)
        self.accion_cortar.setShortcut("Ctrl+X")
        self.accion_cortar.triggered.connect(lambda: self.obtener_editor_activo().text_editor.cut() if self.obtener_editor_activo() else None)

        self.accion_copiar = QAction("&Copiar", self)
        self.accion_copiar.setShortcut("Ctrl+C")
        self.accion_copiar.triggered.connect(lambda: self.obtener_editor_activo().text_editor.copy() if self.obtener_editor_activo() else None)

        self.accion_pegar = QAction("&Pegar", self)
        self.accion_pegar.setShortcut("Ctrl+V")
        self.accion_pegar.triggered.connect(lambda: self.obtener_editor_activo().text_editor.paste() if self.obtener_editor_activo() else None)

        self.accion_buscar = QAction("Buscar...", self)
        self.accion_buscar.setShortcut("Ctrl+F")
        self.accion_buscar.setStatusTip("Muestra la barra de búsqueda")
        self.accion_buscar.triggered.connect(lambda: self.mostrar_barra_busqueda(modo_reemplazar=False))

        self.accion_reemplazar = QAction("Reemplazar...", self)
        self.accion_reemplazar.setShortcut("Ctrl+H")
        self.accion_reemplazar.setStatusTip("Muestra la barra de búsqueda y reemplazo")
        self.accion_reemplazar.triggered.connect(lambda: self.mostrar_barra_busqueda(modo_reemplazar=True))
        
        # 🖥️ Menú Ver
        self.accion_wrap = QAction("&Ajuste de Línea", self)
        self.accion_wrap.setCheckable(True)
        self.accion_wrap.setChecked(False) # Por defecto, sin ajuste (VS Code)
        self.accion_wrap.setShortcut("Alt+Z") # Atajo estilo VS Code
        self.accion_wrap.setStatusTip("Activa/Desactiva el ajuste automático de línea")
        self.accion_wrap.triggered.connect(self.alternar_wrap)

        # Conectar el botón de la barra de actividades
        self.boton_buscar.clicked.connect(self.mostrar_u_ocultar_busqueda)
        
    def alternar_wrap(self, checked):
        """Alterna el modo de ajuste de texto."""
        editor = self.obtener_editor_activo()
        if not editor: return
        if checked:
            # Ajustar al ancho de la ventana (el equivalente es WordWrap)
            editor.text_editor.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            # Sin ajuste (comportamiento estándar de codificación)
            editor.text_editor.setWordWrapMode(QTextOption.WrapMode.NoWrap)

    def crear_acciones(self):
        # 📂 Menú Archivo
        self.accion_abrir = QAction("&Abrir...", self)
        self.accion_abrir.setShortcut("Ctrl+O")
        self.accion_abrir.setStatusTip("Abrir un archivo de texto")
        self.accion_abrir.triggered.connect(self.abrir_archivo)

        self.accion_guardar = QAction("&Guardar", self)
        self.accion_guardar.setShortcut("Ctrl+S")
        self.accion_guardar.setStatusTip("Guardar el archivo actual")
        self.accion_guardar.triggered.connect(self.guardar_archivo)
        
        # Acción Guardar Como
        self.accion_guardar_como = QAction("Guardar &Como...", self)
        self.accion_guardar_como.setShortcut("Ctrl+Shift+S")
        self.accion_guardar_como.setStatusTip("Guardar el contenido en un nuevo archivo")
        self.accion_guardar_como.triggered.connect(self.guardar_como)

        self.accion_salir = QAction("&Salir", self)
        self.accion_salir.setShortcut("Ctrl+Q")
        self.accion_salir.setStatusTip("Cerrar la aplicación")
        self.accion_salir.triggered.connect(self.close)

    def crear_barra_menu(self):
        # 🟢 Usamos nuestra BarraDeTitulo personalizada
        menu_bar = self.BarraDeTitulo(self)
        self.setMenuBar(menu_bar)
        
        # 📂 Menú Archivo
        menu_archivo = menu_bar.addMenu("&Archivo")
        menu_archivo.addAction(self.accion_abrir)
        menu_archivo.addAction(self.accion_guardar)
        menu_archivo.addAction(self.accion_guardar_como)
        menu_archivo.addSeparator()  # Línea separadora
        menu_archivo.addAction(self.accion_salir)

        # 📝 Menú Editar
        menu_editar = menu_bar.addMenu("&Editar")
        menu_editar.addAction(self.accion_deshacer)
        menu_editar.addAction(self.accion_rehacer)
        menu_editar.addSeparator()
        menu_editar.addAction(self.accion_cortar)
        menu_editar.addAction(self.accion_copiar)
        menu_editar.addAction(self.accion_pegar)
        menu_editar.addSeparator()
        menu_editar.addAction(self.accion_buscar)
        menu_editar.addAction(self.accion_reemplazar)

        # 🖥️ Menú Ver
        menu_ver = menu_bar.addMenu("&Ver")
        menu_ver.addAction(self.accion_wrap)

        # --- Controles de Ventana (Minimizar, Maximizar, Cerrar) ---
        controles_ventana_widget = QWidget()
        layout_controles = QHBoxLayout(controles_ventana_widget)
        layout_controles.setContentsMargins(0, 0, 10, 0) # Margen derecho
        layout_controles.setSpacing(10)

        boton_minimizar = QPushButton("—")
        boton_maximizar = QPushButton("▢")
        boton_cerrar = QPushButton("✕")

        estilo_controles = """
            QPushButton {
                background-color: transparent;
                color: #F8F8F2;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 2px 5px;
            }
            QPushButton:hover {
                background-color: #44475A;
            }
            QPushButton#close_button:hover {
                background-color: #FF5555;
            }
        """
        boton_cerrar.setObjectName("close_button") # Para estilo específico
        for boton in [boton_minimizar, boton_maximizar, boton_cerrar]:
            boton.setStyleSheet(estilo_controles)
            layout_controles.addWidget(boton)

        boton_minimizar.clicked.connect(self.showMinimized)
        boton_maximizar.clicked.connect(self.alternar_maximizado)
        boton_cerrar.clicked.connect(self.close)

        menu_bar.setCornerWidget(controles_ventana_widget, Qt.Corner.TopRightCorner)

    def crear_barra_estado(self):
        self.barra_estado = QStatusBar()
        self.setStatusBar(self.barra_estado)

        # --- Widgets para la parte derecha de la barra de estado ---
        self.label_posicion_cursor = QLabel("Línea: 1, Col: 1")
        self.label_contador_caracteres = QLabel("Caracteres: 0")
        self.label_encoding = QLabel("UTF-8")
        self.label_lenguaje = QLabel("Texto Plano")

        # Añadir widgets permanentes a la derecha (se añaden de derecha a izquierda)
        self.barra_estado.addPermanentWidget(self.label_posicion_cursor)
        self.barra_estado.addPermanentWidget(self.label_contador_caracteres)
        self.barra_estado.addPermanentWidget(self.label_encoding)
        self.barra_estado.addPermanentWidget(self.label_lenguaje)

        # Actualizar los contadores iniciales
        self.actualizar_estado_completo()

    # --- MÉTODOS PARA PANELES ---
    def alternar_panel_explorador(self):
        """Muestra u oculta el panel del explorador de archivos."""
        if self.dock_explorador.isVisible():
            self.dock_explorador.hide()
        else:
            self.dock_explorador.show()
            
    def alternar_maximizado(self):
        """Maximiza la ventana si está en modo normal, o la restaura si está maximizada."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = VentanaPrincipal()
    sys.exit(app.exec())
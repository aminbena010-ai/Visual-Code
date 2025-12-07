import subprocess
import os
import sys

# --- CONFIGURACIÓN ---
VENV_NAME = "Visual Code"
PYTHON_SCRIPT = "VisualCode.py"
# Si tu script principal se llama diferente, cámbialo aquí.

def ejecutar_comando(comando, mensaje_error):
    """Ejecuta un comando en el shell y maneja posibles errores."""
    try:
        # Ejecuta el comando y captura la salida
        proceso = subprocess.run(
            comando,
            check=True,  # Lanza una excepción si el código de retorno no es 0
            shell=True,
            capture_output=True,
            text=True
        )
        print(proceso.stdout)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {mensaje_error}")
        print(f"Salida del error:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[ERROR] El comando '{comando[0]}' no fue encontrado.")
        print("Asegúrate de que Python esté instalado y en el PATH.")
        sys.exit(1)

def main():
    """Función principal del script de compilación."""
    print("==================================================")
    print("          SCRIPT DE COMPILACIÓN PYTHON")
    print("==================================================")
    print(f"\n[INFO] Archivo a compilar: {PYTHON_SCRIPT}")

    # --- Rutas del Venv (asume Windows para el PATH de Scripts) ---
    venv_path = os.path.join(os.getcwd(), VENV_NAME)
    pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    pyinstaller_exe = os.path.join(venv_path, "Scripts", "pyinstaller.exe")

    # --- 1. Verificar y crear el entorno virtual (Venv) ---
    if not os.path.exists(pip_exe):
        print(f"\n[INFO] Creando entorno virtual '{VENV_NAME}'...")
        # Comando: python -m venv principal
        ejecutar_comando(
            ["python", "-m", "venv", VENV_NAME],
            "No se pudo crear el entorno virtual. Asegúrate de que Python esté en el PATH."
        )
    else:
        print(f"\n[INFO] Usando entorno virtual existente '{VENV_NAME}'.")

    # --- 2. Instalar dependencias ---
    print("\n[INFO] Instalando dependencias (PyQt6 y PyInstaller)...")
    # Comando: <venv_path>/Scripts/pip.exe install PyQt6 pyinstaller
    ejecutar_comando(
        [pip_exe, "install", "PyQt6", "pyinstaller"],
        "No se pudieron instalar las dependencias. Revisa tu conexión a internet o los permisos."
    )

    # --- 3. Ejecutar PyInstaller ---
    if not os.path.exists(PYTHON_SCRIPT):
        print(f"\n[ERROR] No se encuentra el archivo de script: '{PYTHON_SCRIPT}'.")
        print("Asegúrate de que esté en el mismo directorio.")
        sys.exit(1)

    print(f"\n[INFO] Compilando la aplicación con PyInstaller...")
    # Comando: <venv_path>/Scripts/pyinstaller.exe --noconfirm --onefile --windowed EditorDeTexto.py
    ejecutar_comando(
        [pyinstaller_exe, "--noconfirm", "--onefile", "--windowed", PYTHON_SCRIPT],
        "La compilación con PyInstaller ha fallado."
    )

    # --- Proceso finalizado ---
    output_exe = f"{os.path.splitext(PYTHON_SCRIPT)[0]}.exe"
    print("\n==================================================")
    print("          PROCESO DE COMPILACIÓN FINALIZADO")
    print("==================================================")
    print(f"✅ Tu aplicación '{output_exe}' se encuentra en la carpeta 'dist'.")

if __name__ == "__main__":
    main()
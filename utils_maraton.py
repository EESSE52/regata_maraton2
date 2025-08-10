# utils_maraton.py
# Funciones auxiliares para el Gestor de Regatas.

import sys
import os

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta al recurso. Funciona para desarrollo y para
    aplicaciones empaquetadas con PyInstaller o Nuitka.
    """
    try:
        # PyInstaller/Nuitka crea una carpeta temporal y almacena su ruta en sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Si sys._MEIPASS no está definido, estamos en modo de desarrollo normal.
        try:
            # La ruta base es el directorio del script principal.
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        except Exception:
            # Fallback si sys.argv[0] no está disponible.
            base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

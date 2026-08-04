import os
import getpass

# DIRECCIÓN IP Y PUERTO DEL SERVIDOR LOCAL
SERVER_IP = "192.168.5.74"
SERVER_PORT = 5000

SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# Obtiene automáticamente el nombre del usuario de la computadora
try:
    NOMBRE_USUARIO_PC = os.getlogin()
except Exception:
    NOMBRE_USUARIO_PC = getpass.getuser()
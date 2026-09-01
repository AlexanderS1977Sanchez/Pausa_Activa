import os
import getpass

# IP Servidor en Red Local (Ajusta con la IP real de tu servidor)
SERVER_IP = "192.168.5.74"
SERVER_PORT = 5000
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# Obtención segura del nombre de usuario de la PC cliente
try:
    NOMBRE_USUARIO_PC = os.getlogin()
except Exception:
    NOMBRE_USUARIO_PC = getpass.getuser()
import os
import sys
import pydirectinput
import pyautogui
import ctypes
import time
import random
import winsound

# Forzar escala 1:1 en pantalla para evitar desajustes de resolución
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

pydirectinput.PAUSE = 0.04

# -------------------------------------------------------------
# RUTAS DE RECURSOS (COMPATIBLE CON .PY Y .EXE DE PYINSTALLER)
# -------------------------------------------------------------
def obtener_ruta_recurso(nombre_archivo):
    """
    Obtiene la ruta absoluta del recurso.
    Si se ejecuta como .exe generado por PyInstaller, usa la carpeta temporal _MEIPASS.
    Si se ejecuta como script normal .py, usa el directorio donde reside el archivo.
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, nombre_archivo)

IMG_BOTON_ROLL      = obtener_ruta_recurso('boton_roll.png')
IMG_PALABRA_SECRETO = obtener_ruta_recurso('palabra_secreto.png')

# Comprobación de seguridad para verificar que las imágenes existan
archivos_requeridos = [
    (IMG_BOTON_ROLL, 'boton_roll.png'),
    (IMG_PALABRA_SECRETO, 'palabra_secreto.png')
]

for ruta, nombre in archivos_requeridos:
    if not os.path.exists(ruta):
        ctypes.windll.user32.MessageBoxW(
            0,
            f"No se encontró el archivo: {nombre}\n\nRuta buscada:\n{ruta}",
            "Error de Archivo Requerido",
            0x10  # Ícono de error (MB_ICONERROR)
        )
        sys.exit(1)

# Tolerancia de coincidencia de imagen
CONFIANZA_ROLL    = 0.82
CONFIANZA_SECRETO = 0.80

# Distancias relativas en la fila
OFFSET_DESCARTAR_X  = 368
POS_CONFIRMAR_MODAL = (833, 648)  # Botón rojo modal Mítico

# Teclas de control
VK_F7 = 0x76  # Iniciar
VK_F8 = 0x77  # Pausar

def mostrar_instrucciones():
    """Muestra una ventana emergente nativa con las instrucciones de uso."""
    mensaje = (
        "INSTRUCCIONES DE USO:\n\n"
        "1. Debes estar en la pestaña TRIPULACIÓN.\n"
        "2. Ten visible la RANURA VACÍA con la opción PROFESIONAL $10M.\n"
        "3. Controles:\n"
        "   - Presiona [ F7 ] para COMENZAR el auto-roll.\n"
        "   - Presiona [ F8 ] para PAUSAR / DETENER en cualquier momento.\n\n"
        "4. Al conseguir un tripulante SECRETO, el bot sonará y se detendrá solo.\n"
        "   (Cuando obtengas el tripulante, reinicia el programa si deseas continuar farmeando).\n\n"
        "Haz clic en Aceptar cuando el juego esté listo."
    )
    titulo = "Auto-Roll Roblox - Instrucciones"
    # 0x40 = Ícono de Información (MB_ICONINFORMATION) + Botón Aceptar (MB_OK)
    ctypes.windll.user32.MessageBoxW(0, mensaje, titulo, 0x40)

def tecla_presionada(codigo):
    return (ctypes.windll.user32.GetAsyncKeyState(codigo) & 0x8000) != 0

def click_hardware(x, y):
    """Mueve con DirectInput y hace un clic físico seguro."""
    pydirectinput.moveTo(int(x), int(y))
    time.sleep(0.05)
    pydirectinput.moveRel(2, 0)
    time.sleep(0.02)
    pydirectinput.moveRel(-2, 0)
    time.sleep(0.04)
    pydirectinput.mouseDown()
    time.sleep(random.uniform(0.10, 0.14))
    pydirectinput.mouseUp()
    time.sleep(0.05)

def es_secreto_en_fila(y_centro_fila):
    """
    Busca la palabra 'SECRETO' exclusivamente en la franja horizontal
    de la fila actual (y_centro_fila +- 50 px).
    """
    try:
        alto_pantalla = pyautogui.size().height
        ancho_pantalla = pyautogui.size().width

        y_inicio = max(0, int(y_centro_fila - 50))
        alto_franja = min(100, alto_pantalla - y_inicio)

        region_fila = (0, y_inicio, ancho_pantalla, alto_franja)

        match = pyautogui.locateOnScreen(
            IMG_PALABRA_SECRETO,
            region=region_fila,
            confidence=CONFIANZA_SECRETO
        )
        return match is not None
    except Exception:
        return False

def obtener_color_pantalla(x, y):
    hdc = ctypes.windll.user32.GetDC(0)
    color = ctypes.windll.gdi32.GetPixel(hdc, int(x), int(y))
    ctypes.windll.user32.ReleaseDC(0, hdc)
    return (color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF)

def main():
    # Mostrar el cuadro emergente con instrucciones antes de iniciar
    mostrar_instrucciones()

    print("=" * 65)
    print("[*] BOT CON DETECCIÓN POR PALABRA CLAVE 'SECRETO'")
    print("[*] Recursos verificados y listos.")
    print("[*] Presiona [ F7 ] para INICIAR | [ F8 ] para PAUSAR")
    print("=" * 65)

    activo = False
    tiradas = 0

    try:
        while True:
            # Iniciar con F7
            if not activo and tecla_presionada(VK_F7):
                activo = True
                print("\n[>>>] AUTO-ROLL ACTIVADO...")
                winsound.Beep(1200, 150)
                time.sleep(0.4)

            # Pausar con F8
            if activo and tecla_presionada(VK_F8):
                activo = False
                print("\n[|||] BOT PAUSADO con F8.")
                winsound.Beep(700, 250)
                time.sleep(0.4)

            if activo:
                # 1. Localizar la ranura activa buscando el botón de Roll
                try:
                    ubicacion_roll = pyautogui.locateOnScreen(IMG_BOTON_ROLL, confidence=CONFIANZA_ROLL)
                except Exception:
                    ubicacion_roll = None

                if ubicacion_roll is None:
                    print("    [?] Esperando que aparezca el botón de roll...")
                    time.sleep(0.4)
                    continue

                roll_x, roll_y = pyautogui.center(ubicacion_roll)
                pos_descartar = (roll_x + OFFSET_DESCARTAR_X, roll_y)

                tiradas += 1
                print(f"\n[+] Tirada #{tiradas} en fila Y={roll_y}...")
                click_hardware(roll_x, roll_y)

                # Pausa para que termine la animación de revelación del secuaz
                time.sleep(0.65)

                # 2. Comprobar si la palabra SECRETO está en esa línea horizontal
                if es_secreto_en_fila(roll_y):
                    print("\n" + "#" * 60)
                    print(f">>> ¡¡¡SECRETO CONFIRMADO EN FILA Y={roll_y}!!! NO SE DESCARTA <<<")
                    print("#" * 60)
                    for _ in range(6):
                        winsound.Beep(1500, 180)
                        time.sleep(0.06)
                        winsound.Beep(2100, 350)
                    
                    # Mensaje emergente avisando que se consiguió
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        "¡¡¡TRIPULANTE SECRETO OBTENIDO!!!\n\nEl bot se ha detenido para proteger tu tripulante.",
                        "¡Éxito!",
                        0x40
                    )
                    activo = False
                    break

                # 3. Si no es secreto, descartar de la fila activa
                click_hardware(*pos_descartar)
                time.sleep(random.uniform(0.18, 0.28))
                click_hardware(*pos_descartar)
                time.sleep(0.25)

                # 4. Modal de confirmación (si salió un Mítico)
                mr, mg, mb = obtener_color_pantalla(*POS_CONFIRMAR_MODAL)
                if mr > 120 and mg < 70 and mb < 70:
                    click_hardware(*POS_CONFIRMAR_MODAL)
                    time.sleep(random.uniform(0.3, 0.45))
                else:
                    time.sleep(random.uniform(0.08, 0.15))

            time.sleep(0.03)

    except KeyboardInterrupt:
        print("\n[!] Proceso finalizado.")

if __name__ == "__main__":
    main()
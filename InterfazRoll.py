#Se creara una interfaz interactiva en la cual el usuario podra asignar las teclas de inicio y pausa
#Podra decidir si hara roll tripulante eligiendo (Precio y calidad) Secreto/Mitico
#Eligira el boton de compra, si gastara 1M o 10M
#Se agregara roll tienda, se compraran objetos hasta epico y si el usuario lo decide, tambien se comprarn leyendarios(no se compra nada con oro)
#Por ultimo se agregara farmeo de trabajos usando energia
#Se guardara el dinero automaticamente si detecta tener cierta cantidad.

import os
import sys
import threading
import time
import random
import winsound
import ctypes
import numpy as np
from PIL import Image, ImageTk, ImageGrab
import pyautogui
import pydirectinput
import tkinter as tk
from tkinter import messagebox, ttk

# -------------------------------------------------------------
# CONFIGURACIÓN DE SISTEMA Y DPI

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

try:
    mi_app_id = 'miempresa.miapp.subproducto.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(mi_app_id)
except Exception:
    pass

pydirectinput.PAUSE = 0.04
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True

# -------------------------------------------------------------
# RUTAS DE RECURSOS

def obtener_ruta_recurso(nombre_archivo):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, nombre_archivo)

RUTA_ICONO = obtener_ruta_recurso('LuminicLogo.png')
RUTA_LUMINIC = obtener_ruta_recurso('LuminicImg.png')
if not os.path.exists(RUTA_LUMINIC):
    RUTA_LUMINIC = "c:/Users/JOSE/Documents/Codigos Py/LuminicImg.png"

IMG_BOTON_ROLL            = obtener_ruta_recurso('boton_roll.png')
IMG_PALABRA_SECRETO       = obtener_ruta_recurso('palabra_secreto.png')
IMG_BOTON_DESCARTAR_FILA  = obtener_ruta_recurso('boton_descartar.png')
IMG_BOTON_DESCARTAR_MODAL = obtener_ruta_recurso('boton_descartar_modal.png')
TEMPLATE_COMPRAR          = obtener_ruta_recurso('comprar_btn.png')

archivos_requeridos = [
    (RUTA_ICONO, 'LuminicLogo.png'),
    (IMG_BOTON_ROLL, 'boton_roll.png'),
    (IMG_PALABRA_SECRETO, 'palabra_secreto.png'),
    (IMG_BOTON_DESCARTAR_FILA, 'boton_descartar.png'),
    (IMG_BOTON_DESCARTAR_MODAL, 'boton_descartar_modal.png'),
    (TEMPLATE_COMPRAR, 'comprar_btn.png')
]

for ruta, nombre in archivos_requeridos:
    if not os.path.exists(ruta):
        ctypes.windll.user32.MessageBoxW(
            0,
            f"No se encontró el archivo requerido: {nombre}\n\nRuta buscada:\n{ruta}",
            "Error de Archivo Requerido",
            0x10
        )
        sys.exit(1)

# -------------------------------------------------------------
# DICCIONARIO DE TECLAS VIRTUALES (VK)

TECLAS_DISPONIBLES = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "P": 0x50, "O": 0x4F, "I": 0x49, "U": 0x55,
    "K": 0x4B, "L": 0x4C, "J": 0x4A, "H": 0x48,
    "Q": 0x51, "X": 0x58, "C": 0x43, "V": 0x56, "B": 0x42
}

CONFIG_HOTKEYS = {
    "INICIAR_NOMBRE": "F7",
    "INICIAR_VK": 0x76,
    "PAUSAR_NOMBRE": "F8",
    "PAUSAR_VK": 0x77
}

CONFIANZA_ROLL      = 0.82
CONFIANZA_SECRETO   = 0.80
CONFIANZA_DESCARTAR = 0.80
CONFIANZA_MODAL     = 0.78
OFFSET_DESCARTAR_X  = 368

# -------------------------------------------------------------
# CONTROL DE EXCLUSIÓN MUTUA DE MODOS

# modo_seleccionado: 'tripulante' | 'tienda' | None
modo_seleccionado = None
tripulante_corriendo = False
tienda_corriendo = False

def tecla_presionada(codigo):
    return (ctypes.windll.user32.GetAsyncKeyState(codigo) & 0x8000) != 0

def click_hardware(x, y):
    """Clic compatible con Roblox por hardware (DirectInput)."""
    pydirectinput.moveTo(int(x), int(y))
    time.sleep(0.04)
    pydirectinput.moveRel(2, 0)
    time.sleep(0.02)
    pydirectinput.moveRel(-2, 0)
    time.sleep(0.03)
    pydirectinput.mouseDown()
    time.sleep(random.uniform(0.09, 0.13))
    pydirectinput.mouseUp()
    time.sleep(0.04)

def scroll_nativo(clicks):
    ctypes.windll.user32.mouse_event(0x0800, 0, 0, clicks * 120, 0)

# -------------------------------------------------------------
# MÓDULO AUTO-COMPRA (TIENDA)

def es_compra_valida(boton_box):
    bx, by, bw, bh = boton_box

    area_precio = (bx - 10, max(0, by - 35), bx + bw + 10, by)
    captura_precio = np.array(ImageGrab.grab(bbox=area_precio))

    es_verde = (
        (captura_precio[:, :, 0] < 140) & 
        (captura_precio[:, :, 1] > 160) & 
        (captura_precio[:, :, 2] < 160)
    )
    if np.sum(es_verde) < 6:
        return False

    area_icono = (max(0, bx - 320), by - 15, max(0, bx - 180), by + bh + 15)
    captura_icono = np.array(ImageGrab.grab(bbox=area_icono))

    es_dorado = (
        (captura_icono[:, :, 0] > 180) & 
        (captura_icono[:, :, 1] > 140) & 
        (captura_icono[:, :, 2] < 80)
    )
    if np.sum(es_dorado) > 30:
        return False

    return True

def procesar_compras():
    global tienda_corriendo, modo_seleccionado
    try:
        botones = list(pyautogui.locateAllOnScreen(TEMPLATE_COMPRAR, confidence=0.80))
        botones_unicos = []
        for b in botones:
            if not any(abs(b.top - u.top) < 12 for u in botones_unicos):
                botones_unicos.append(b)

        pantalla_ancho, _ = pyautogui.size()
        for b in botones_unicos:
            if modo_seleccionado != 'tienda' or not tienda_corriendo or tecla_presionada(CONFIG_HOTKEYS["PAUSAR_VK"]):
                return

            if b.left > (pantalla_ancho * 0.55):
                continue

            if es_compra_valida(b):
                cx, cy = pyautogui.center(b)
                print(f" -> Clic de hardware en tienda: ({cx}, {cy})")
                click_hardware(cx, cy)
                time.sleep(0.12)
    except Exception as e:
        print(f"Error procesando compras: {e}")

def ciclo_tienda():
    global tienda_corriendo, modo_seleccionado
    print("\n--- Iniciando ciclo de tienda ---")
    pantalla_ancho, pantalla_alto = pyautogui.size()
    scroll_x = int(pantalla_ancho * 0.30)
    scroll_y = int(pantalla_alto * 0.55)

    click_hardware(scroll_x, scroll_y)
    time.sleep(0.2)

    for _ in range(6):
        if modo_seleccionado != 'tienda' or not tienda_corriendo or tecla_presionada(CONFIG_HOTKEYS["PAUSAR_VK"]):
            return
        scroll_nativo(3)
        time.sleep(0.04)
    time.sleep(0.3)

    pasos_totales = 6
    for paso in range(pasos_totales):
        if modo_seleccionado != 'tienda' or not tienda_corriendo or tecla_presionada(CONFIG_HOTKEYS["PAUSAR_VK"]):
            print("[|||] Tienda interrumpida durante el scroll.")
            return

        print(f"[Tienda: Paso {paso + 1}/{pasos_totales}]")
        procesar_compras()

        if modo_seleccionado != 'tienda' or not tienda_corriendo or tecla_presionada(CONFIG_HOTKEYS["PAUSAR_VK"]):
            return

        pydirectinput.moveTo(scroll_x, scroll_y)
        for _ in range(2):
            scroll_nativo(-2)
            time.sleep(0.06)
        time.sleep(0.25)

    if modo_seleccionado != 'tienda' or not tienda_corriendo or tecla_presionada(CONFIG_HOTKEYS["PAUSAR_VK"]):
        return

    print("[Tienda: Paso final]")
    procesar_compras()

    pydirectinput.moveTo(scroll_x, scroll_y)
    for _ in range(6):
        scroll_nativo(3)
        time.sleep(0.04)
    print("--- Ciclo de tienda finalizado ---\n")

def bucle_tienda():
    global tienda_corriendo, modo_seleccionado
    while True:
        if modo_seleccionado == 'tienda':
            vk_iniciar = CONFIG_HOTKEYS["INICIAR_VK"]
            vk_pausar = CONFIG_HOTKEYS["PAUSAR_VK"]

            if not tienda_corriendo and tecla_presionada(vk_iniciar):
                tienda_corriendo = True
                print(f"\n[>>>] TIENDA ACTIVADA con {CONFIG_HOTKEYS['INICIAR_NOMBRE']}...")
                winsound.Beep(1200, 150)
                time.sleep(0.35)

            if tienda_corriendo and tecla_presionada(vk_pausar):
                tienda_corriendo = False
                print(f"\n[|||] TIENDA PAUSADA con {CONFIG_HOTKEYS['PAUSAR_NOMBRE']}.")
                winsound.Beep(700, 250)
                time.sleep(0.35)

            if tienda_corriendo:
                ciclo_tienda()
                time.sleep(0.8)

        time.sleep(0.03)

# -------------------------------------------------------------
# MÓDULO AUTO-ROLL (TRIPULANTES)

def es_secreto_en_fila(y_centro_fila):
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

def obtener_posicion_descartar(y_centro_fila, x_roll):
    try:
        alto_pantalla = pyautogui.size().height
        ancho_pantalla = pyautogui.size().width
        y_inicio = max(0, int(y_centro_fila - 45))
        alto_franja = min(90, alto_pantalla - y_inicio)
        region_fila = (0, y_inicio, ancho_pantalla, alto_franja)

        coord = pyautogui.locateCenterOnScreen(
            IMG_BOTON_DESCARTAR_FILA,
            region=region_fila,
            confidence=CONFIANZA_DESCARTAR
        )
        if coord is not None:
            return coord.x, coord.y
    except Exception:
        pass
    return (x_roll + OFFSET_DESCARTAR_X, y_centro_fila)

def bucle_tripulantes():
    global tripulante_corriendo, modo_seleccionado
    tiradas = 0

    while True:
        if modo_seleccionado == 'tripulante':
            vk_iniciar = CONFIG_HOTKEYS["INICIAR_VK"]
            vk_pausar = CONFIG_HOTKEYS["PAUSAR_VK"]

            if not tripulante_corriendo and tecla_presionada(vk_iniciar):
                tripulante_corriendo = True
                print(f"\n[>>>] AUTO-ROLL ACTIVADO con {CONFIG_HOTKEYS['INICIAR_NOMBRE']}...")
                winsound.Beep(1200, 150)
                time.sleep(0.35)

            if tripulante_corriendo and tecla_presionada(vk_pausar):
                tripulante_corriendo = False
                print(f"\n[|||] BOT TRIPULANTES PAUSADO con {CONFIG_HOTKEYS['PAUSAR_NOMBRE']}.")
                winsound.Beep(700, 250)
                time.sleep(0.35)

            if tripulante_corriendo:
                try:
                    ubicacion_roll = pyautogui.locateOnScreen(IMG_BOTON_ROLL, confidence=CONFIANZA_ROLL)
                except Exception:
                    ubicacion_roll = None

                if modo_seleccionado != 'tripulante' or not tripulante_corriendo:
                    continue

                if ubicacion_roll is None:
                    try:
                        modal_colgado = pyautogui.locateCenterOnScreen(IMG_BOTON_DESCARTAR_MODAL, confidence=CONFIANZA_MODAL)
                    except Exception:
                        modal_colgado = None

                    if modal_colgado is not None:
                        click_hardware(modal_colgado.x, modal_colgado.y)
                        time.sleep(0.35)
                        continue

                    time.sleep(0.3)
                    continue

                roll_x, roll_y = pyautogui.center(ubicacion_roll)
                tiradas += 1
                print(f"\n[+] Tirada #{tiradas} en fila Y={roll_y}...")
                click_hardware(roll_x, roll_y)
                time.sleep(0.65)

                if modo_seleccionado != 'tripulante' or not tripulante_corriendo:
                    continue

                if es_secreto_en_fila(roll_y):
                    print("\n" + "#" * 60)
                    print(f">>> SECRETO CONFIRMADO EN FILA Y={roll_y} <<<")
                    print("#" * 60)
                    for _ in range(5):
                        winsound.Beep(1500, 150)
                        time.sleep(0.05)
                        winsound.Beep(2100, 250)

                    tripulante_corriendo = False
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        f"¡¡¡TRIPULANTE SECRETO OBTENIDO!!!\n\nEl bot se ha pausado para protegerlo.\nPrepara la ranura y presiona [{CONFIG_HOTKEYS['INICIAR_NOMBRE']}] para continuar.",
                        "¡Éxito!",
                        0x40
                    )
                    time.sleep(0.5)
                    continue

                descartar_x, descartar_y = obtener_posicion_descartar(roll_y, roll_x)
                click_hardware(descartar_x, descartar_y)
                time.sleep(0.35)

                try:
                    ubicacion_modal = pyautogui.locateCenterOnScreen(
                        IMG_BOTON_DESCARTAR_MODAL,
                        confidence=CONFIANZA_MODAL
                    )
                except Exception:
                    ubicacion_modal = None

                if ubicacion_modal is not None:
                    click_hardware(ubicacion_modal.x, ubicacion_modal.y)
                    time.sleep(random.uniform(0.35, 0.45))
                else:
                    click_hardware(descartar_x, descartar_y)
                    time.sleep(random.uniform(0.12, 0.20))

        time.sleep(0.03)

# Iniciar los dos bucles daemon en segundo plano una sola vez
threading.Thread(target=bucle_tripulantes, daemon=True).start()
threading.Thread(target=bucle_tienda, daemon=True).start()

# -------------------------------------------------------------
# CONTROLADORES DE SELECCIÓN EXCLUSIVA (UI)

def actualizar_estilos_botones():
    if modo_seleccionado == 'tripulante':
        btn_Tripulante.config(bg="#1b5e20", fg="white", text="✓ Tripulante Activo")
        btn_Tienda.config(bg="#e0e0e0", fg="black", text="Roll tienda")
    elif modo_seleccionado == 'tienda':
        btn_Tienda.config(bg="#1b5e20", fg="white", text="✓ Tienda Activa")
        btn_Tripulante.config(bg="#e0e0e0", fg="black", text="Roll tripulante")
    else:
        btn_Tripulante.config(bg="#e0e0e0", fg="black", text="Roll tripulante")
        btn_Tienda.config(bg="#e0e0e0", fg="black", text="Roll tienda")

def seleccionar_modo_tripulante():
    global modo_seleccionado, tripulante_corriendo, tienda_corriendo
    # Detener tienda por completo
    tienda_corriendo = False
    modo_seleccionado = 'tripulante'
    tripulante_corriendo = False
    actualizar_estilos_botones()
    print("\n[MODO CAMBIADO] -> Auto-Roll TRIPULANTES seleccionado.")
    messagebox.showinfo(
        "Modo Tripulantes",
        f"Modo TRIPULANTES activado (Tienda detenida).\n\n"
        f"Presiona [{CONFIG_HOTKEYS['INICIAR_NOMBRE']}] para rodar.\n"
        f"Presiona [{CONFIG_HOTKEYS['PAUSAR_NOMBRE']}] para pausar."
    )

def seleccionar_modo_tienda():
    global modo_seleccionado, tripulante_corriendo, tienda_corriendo
    # Detener tripulantes por completo
    tripulante_corriendo = False
    modo_seleccionado = 'tienda'
    tienda_corriendo = False
    actualizar_estilos_botones()
    print("\n[MODO CAMBIADO] -> Auto-Compra TIENDA seleccionada.")
    messagebox.showinfo(
        "Modo Tienda",
        f"Modo TIENDA activado (Tripulantes detenido).\n\n"
        f"Presiona [{CONFIG_HOTKEYS['INICIAR_NOMBRE']}] para comenzar.\n"
        f"Presiona [{CONFIG_HOTKEYS['PAUSAR_NOMBRE']}] para pausar."
    )

# -------------------------------------------------------------
# VENTANA DE CONFIGURACIÓN DE TECLAS

def abrir_ventana_configuracion(parent):
    config_win = tk.Toplevel(parent)
    config_win.title("Configurar Teclas")
    config_win.geometry("320x220")
    config_win.resizable(False, False)
    config_win.grab_set()

    lbl_info = tk.Label(
        config_win,
        text="Teclas de control (compartidas por ambos bots):",
        font=("Arial", 9, "bold"),
        pady=10
    )
    lbl_info.pack()

    frame_form = tk.Frame(config_win)
    frame_form.pack(pady=5)

    tk.Label(frame_form, text="Iniciar / Reanudar:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
    combo_iniciar = ttk.Combobox(frame_form, values=list(TECLAS_DISPONIBLES.keys()), width=10, state="readonly")
    combo_iniciar.set(CONFIG_HOTKEYS["INICIAR_NOMBRE"])
    combo_iniciar.grid(row=0, column=1, padx=8, pady=8)

    tk.Label(frame_form, text="Pausar / Detener:").grid(row=1, column=0, padx=8, pady=8, sticky="e")
    combo_pausar = ttk.Combobox(frame_form, values=list(TECLAS_DISPONIBLES.keys()), width=10, state="readonly")
    combo_pausar.set(CONFIG_HOTKEYS["PAUSAR_NOMBRE"])
    combo_pausar.grid(row=1, column=1, padx=8, pady=8)

    def guardar_config():
        tecla_ini = combo_iniciar.get()
        tecla_pau = combo_pausar.get()

        if tecla_ini == tecla_pau:
            messagebox.showerror("Error", "La tecla de inicio y la de pausa deben ser distintas.", parent=config_win)
            return

        CONFIG_HOTKEYS["INICIAR_NOMBRE"] = tecla_ini
        CONFIG_HOTKEYS["INICIAR_VK"] = TECLAS_DISPONIBLES[tecla_ini]
        CONFIG_HOTKEYS["PAUSAR_NOMBRE"] = tecla_pau
        CONFIG_HOTKEYS["PAUSAR_VK"] = TECLAS_DISPONIBLES[tecla_pau]

        messagebox.showinfo("Guardado", f"Nuevas teclas asignadas:\nIniciar: [{tecla_ini}]\nPausar: [{tecla_pau}]", parent=config_win)
        config_win.destroy()

    btn_guardar = tk.Button(config_win, text="Guardar Cambios", bg="#2e7d32", fg="white", font=("Arial", 9, "bold"), command=guardar_config, cursor="hand2")
    btn_guardar.pack(pady=15)

# -------------------------------------------------------------
# INTERFAZ GRÁFICA PRINCIPAL DIRECTA (ROOT)

if __name__ == "__main__":
    ANCHO_VENTANA = 450
    ALTO_VENTANA = 520

    root = tk.Tk()
    root.title("Panel de Control")
    root.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
    root.resizable(False, False)

    try:
        img_ico = ImageTk.PhotoImage(file=RUTA_ICONO)
        root.iconphoto(True, img_ico)
    except Exception as e:
        print(f"No se pudo cargar el icono: {e}")

    canvas = tk.Canvas(root, width=ANCHO_VENTANA, height=ALTO_VENTANA, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    try:
        img_original = Image.open(RUTA_LUMINIC)
        img_fondo = img_original.resize((ANCHO_VENTANA, ALTO_VENTANA), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_fondo)
        canvas.create_image(0, 0, image=img_tk, anchor="nw")
        canvas.image = img_tk
    except FileNotFoundError:
        canvas.configure(bg="#2b2b2b")
        canvas.create_text(
            ANCHO_VENTANA // 2, 200, 
            text="No se encontró LuminicImg.png", 
            fill="red", 
            font=("Arial", 12, "bold")
        )

    # Botones principales interactivos
    btn_Tripulante = tk.Button(
        root, 
        text="Roll tripulante", 
        width=17, 
        font=("Arial", 10, "bold"),
        cursor="hand2",
        command=seleccionar_modo_tripulante
    )
    btn_Tienda = tk.Button(
        root,
        text="Roll tienda",
        width=17,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        command=seleccionar_modo_tienda
    )
    btn_Config = tk.Button(
        root,
        text="Configurar Teclas",
        width=17,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        command=lambda: abrir_ventana_configuracion(root)
    )
    btn_cerrar = tk.Button(
        root, 
        text="Cerrar", 
        width=17, 
        font=("Arial", 10, "bold"),
        cursor="hand2",
        command=root.destroy
    )

    canvas.create_window(150, 70, window=btn_Tripulante)
    canvas.create_window(150, 180, window=btn_Tienda)
    canvas.create_window(150, 290, window=btn_Config)
    canvas.create_window(150, 420, window=btn_cerrar)

    root.mainloop()
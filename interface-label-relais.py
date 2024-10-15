# Interface  qui permet de visualiser l'état du relais et de le contrôler
# Il y aura ces boutons :
# - Activer le transfert
# - Désactiver le transfert (si le transfert est en cours)
# - Voir la caméra
# - Voir la camera avec le filtre threshold
# - Voir la caméra avec les contours

# Parametres qui peuvent être modifiés : 
# - transfert_delay (délai en secondes avant d'activer le relais)
# - relay_on_duration (durée en secondes pendant laquelle le relais reste activé)
# - Luminosite
# - Reglage du flou 
# - Balance des blancs

# Reste à faire :
# - Convertir en app 
# - Ajouter la reconnaissance de l'étiquette
# - Systeme d'alertes  (email, sms, slack) quand alerter ? 
# - Ajout d'un selecteur de camera




# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
try:
    from PIL import Image, ImageTk
except ImportError:
    import Image, ImageTk

# Nom du fichier de configuration JSON
CONFIG_FILE = "config.json"

# Fonction pour charger la configuration depuis un fichier JSON
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {
        "transfert_delay": 3,
        "relay_on_duration": 5,
        "luminosite": 128,
        "blur": 9,
        "white_balance": 1.0
    }

# Fonction pour sauvegarder la configuration dans un fichier JSON
def save_config():
    config = {
        "transfert_delay": transfert_delay,
        "relay_on_duration": relay_on_duration,
        "luminosite": luminosite,
        "blur": blur,
        "white_balance": white_balance
    }
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)
    messagebox.showinfo("Configuration", "Configuration sauvegardée avec succès !")

# Charger la configuration
config = load_config()
transfert_delay = config["transfert_delay"]
relay_on_duration = config["relay_on_duration"]
luminosite = config["luminosite"]
blur = config["blur"]
white_balance = config["white_balance"]

# Initialiser la caméra
cap = cv2.VideoCapture(0)

prev_frame_time = 0
new_frame_time = 0

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) // 2
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) // 2
middle_line_x = frame_width // 2

transfer_on_time = 0
transfer_active = False

show_camera = False
show_threshold = False

def toggle_transfer():
    global transfer_active
    transfer_active = not transfer_active

def toggle_camera():
    global show_camera, show_threshold
    show_camera = not show_camera
    show_threshold = False
    camera_button.config(text="Désactiver l'aperçu caméra" if show_camera else "Activer l'aperçu caméra")
    threshold_button.config(text="Voir la caméra avec le filtre threshold")

def toggle_threshold():
    global show_threshold, show_camera
    show_threshold = not show_threshold
    show_camera = False
    threshold_button.config(text="Désactiver le filtre threshold" if show_threshold else "Voir la caméra avec le filtre threshold")
    camera_button.config(text="Activer l'aperçu caméra")

def update_frame():
    global prev_frame_time, new_frame_time, transfer_on_time, transfer_active, luminosite, blur, white_balance

    ret, frame = cap.read()
    
    if not ret:
        return

    # Appliquer la luminosité avant tout traitement
    frame = cv2.convertScaleAbs(frame, alpha=white_balance, beta=luminosite - 128)

    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (blur, blur), 0)
    _, thresh = cv2.threshold(blurred, 130, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cv2.line(frame, (middle_line_x, 0), (middle_line_x, frame.shape[0]), (255, 0, 0), 2)

    transfer_on = False

    for contour in contours:
        area = cv2.contourArea(contour)
        approx = cv2.approxPolyDP(contour, 0.05 * cv2.arcLength(contour, True), True)

        if len(approx) == 4 and area > 10000:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h

            if 0.6 < aspect_ratio < 1.6:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Étiquette détectée", (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, f"Surface: {int(area)}", (x, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, f"Ratio: {round(aspect_ratio, 2)}", (x, y - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                if x < middle_line_x:
                    transfer_on = True

    if transfer_on:
        if not transfer_active:
            transfer_on_time = time.time()
            transfer_active = True
    else:
        transfer_active = False

    if transfer_active and (time.time() - transfer_on_time >= transfert_delay):
        print("Transfert OK")
        cv2.putText(frame, "Transfert OK", (10, frame.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    fps_text = f"FPS: {int(fps)}"
    cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    if show_camera:
        frame_resized = cv2.resize(frame, (frame_width, frame_height))
        img = Image.fromarray(cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)
    elif show_threshold:
        thresh_resized = cv2.resize(thresh, (frame_width, frame_height))
        img_thresh = Image.fromarray(thresh_resized)
        imgtk_thresh = ImageTk.PhotoImage(image=img_thresh)
        video_label.imgtk = imgtk_thresh
        video_label.configure(image=imgtk_thresh)
    else:
        # Afficher un rectangle gris si la camera n'est pas activée
        dark_gray_frame = np.full((frame_height, frame_width, 3), 128, dtype=np.uint8)  # Rempli de gris
        img_dark_gray = Image.fromarray(dark_gray_frame)
        imgtk_dark_gray = ImageTk.PhotoImage(image=img_dark_gray)
        video_label.imgtk = imgtk_dark_gray
        video_label.configure(image=imgtk_dark_gray)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cap.release()
        cv2.destroyAllWindows()
        save_config()  # Sauvegarder la configuration en quittant
        root.quit()
        return

    root.after(10, update_frame)

def update_transfert_delay(value):
    global transfert_delay
    transfert_delay = float(value)
    transfert_delay_entry.delete(0, tk.END)
    transfert_delay_entry.insert(0, str(transfert_delay))

def update_relay_on_duration(value):
    global relay_on_duration
    relay_on_duration = float(value)
    relay_on_duration_entry.delete(0, tk.END)
    relay_on_duration_entry.insert(0, str(relay_on_duration))

def update_luminosite(value):
    global luminosite
    luminosite = int(float(value))
    luminosite_entry.delete(0, tk.END)
    luminosite_entry.insert(0, str(luminosite))

def update_blur(value):
    global blur
    blur = int(float(value))
    if blur % 2 == 0:  # Blur size must be odd
        blur += 1
    blur_entry.delete(0, tk.END)
    blur_entry.insert(0, str(blur))

def update_white_balance(value):
    global white_balance
    white_balance = float(value)
    white_balance_entry.delete(0, tk.END)
    white_balance_entry.insert(0, str(white_balance))

def update_transfert_delay_entry(event):
    value = transfert_delay_entry.get()
    transfert_delay_slider.set(float(value))

def update_relay_on_duration_entry(event):
    value = relay_on_duration_entry.get()
    relay_on_duration_slider.set(float(value))

def update_luminosite_entry(event):
    value = luminosite_entry.get()
    luminosite_slider.set(int(value))

def update_blur_entry(event):
    value = blur_entry.get()
    blur_slider.set(int(value))

def update_white_balance_entry(event):
    value = white_balance_entry.get()
    white_balance_slider.set(float(value))

# Initialiser la fenêtre principale
root = tk.Tk()
root.title("Interface de contrôle du relais")

# Utiliser un thème sombre pour l'interface
style = ttk.Style()
root.tk_setPalette(background='#2E2E2E', foreground='#FFFFFF', activeBackground='#3C3C3C', activeForeground='#FFFFFF')
style.configure('TLabel', background='#2E2E2E', foreground='#FFFFFF')
style.configure('TButton', background='#3C3C3C', foreground='#FFFFFF')
style.configure('TEntry', background='#3C3C3C', foreground='#FFFFFF')
style.configure('TScale', background='#2E2E2E', troughcolor='#3C3C3C')

mainframe = ttk.Frame(root, padding="10 10 10 10", style="TFrame")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Vidéo
video_label = ttk.Label(mainframe)
video_label.grid(column=1, row=1, rowspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))

# Boutons et contrôles
camera_button = ttk.Button(mainframe, text="Activer l'aperçu caméra", command=toggle_camera)
camera_button.grid(column=2, row=2, sticky=tk.W)

threshold_button = ttk.Button(mainframe, text="Voir la caméra avec le filtre threshold", command=toggle_threshold)
threshold_button.grid(column=2, row=3, sticky=tk.W)

save_button = ttk.Button(mainframe, text="Sauvegarder la configuration", command=save_config)
save_button.grid(column=2, row=4, sticky=tk.W)

# Réglages du transfert
ttk.Label(mainframe, text="Réglages du transfert").grid(column=2, row=5, columnspan=2, sticky=tk.W)
ttk.Label(mainframe, text="Délai de transfert (s)").grid(column=2, row=6, sticky=tk.W)
transfert_delay_slider = ttk.Scale(mainframe, from_=1, to=10, orient=tk.HORIZONTAL, command=update_transfert_delay)
transfert_delay_slider.set(transfert_delay)
transfert_delay_slider.grid(column=2, row=7, sticky=(tk.W, tk.E))
transfert_delay_entry = ttk.Entry(mainframe, width=5)  # Réduire la largeur du champ
transfert_delay_entry.grid(column=2, row=7, sticky=(tk.W))
transfert_delay_entry.insert(0, str(transfert_delay))
transfert_delay_entry.bind("<Return>", update_transfert_delay_entry)

ttk.Label(mainframe, text="Durée du relais activé (s)").grid(column=2, row=8, sticky=tk.W)
relay_on_duration_slider = ttk.Scale(mainframe, from_=1, to=10, orient=tk.HORIZONTAL, command=update_relay_on_duration)
relay_on_duration_slider.set(relay_on_duration)
relay_on_duration_slider.grid(column=2, row=9, sticky=(tk.W, tk.E))
relay_on_duration_entry = ttk.Entry(mainframe, width=5)  # Réduire la largeur du champ
relay_on_duration_entry.grid(column=2, row=9, sticky=(tk.W))
relay_on_duration_entry.insert(0, str(relay_on_duration))
relay_on_duration_entry.bind("<Return>", update_relay_on_duration_entry)

# Réglages du flux vidéo
ttk.Label(mainframe, text="Réglages du flux vidéo").grid(column=1, row=5, columnspan=2, sticky=tk.W)
ttk.Label(mainframe, text="Luminosité").grid(column=1, row=6, sticky=tk.W)
luminosite_slider = ttk.Scale(mainframe, from_=0, to=255, orient=tk.HORIZONTAL, command=update_luminosite)
luminosite_slider.set(luminosite)
luminosite_slider.grid(column=1, row=7, sticky=(tk.W, tk.E))
luminosite_entry = ttk.Entry(mainframe, width=5)  # Réduire la largeur du champ
luminosite_entry.grid(column=1, row=7, sticky=(tk.W))
luminosite_entry.insert(0, str(luminosite))
luminosite_entry.bind("<Return>", update_luminosite_entry)

ttk.Label(mainframe, text="Flou (taille du noyau)").grid(column=1, row=8, sticky=tk.W)
blur_slider = ttk.Scale(mainframe, from_=1, to=21, orient=tk.HORIZONTAL, command=update_blur)
blur_slider.set(blur)
blur_slider.grid(column=1, row=9, sticky=(tk.W, tk.E))
blur_entry = ttk.Entry(mainframe, width=5)  # Réduire la largeur du champ
blur_entry.grid(column=1, row=9, sticky=(tk.W))
blur_entry.insert(0, str(blur))
blur_entry.bind("<Return>", update_blur_entry)

ttk.Label(mainframe, text="Balance des blancs").grid(column=1, row=10, sticky=tk.W)
white_balance_slider = ttk.Scale(mainframe, from_=0.5, to=2.0, orient=tk.HORIZONTAL, command=update_white_balance)
white_balance_slider.set(white_balance)
white_balance_slider.grid(column=1, row=11, sticky=(tk.W, tk.E))
white_balance_entry = ttk.Entry(mainframe, width=5)  # Réduire la largeur du champ
white_balance_entry.grid(column=1, row=11, sticky=(tk.W))
white_balance_entry.insert(0, str(white_balance))
white_balance_entry.bind("<Return>", update_white_balance_entry)

for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

# Boucle principale
root.after(10, update_frame)
root.mainloop()

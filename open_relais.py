import RPi.GPIO as GPIO
from tkinter import *

# Configuration des GPIO
GPIO.setmode(GPIO.BCM)  # Mode de numérotation des GPIO par numéro BCM

# Définir le numéro de la broche GPIO reliée au relais
RELAY_PIN = 24  # Broche reliée à l'entrée IN du relais (GPIO 24 = Pin 18)

# Configuration de la broche en sortie
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Initialisation du relais (éteint au départ)
GPIO.output(RELAY_PIN, GPIO.LOW)

# Fonction pour allumer/éteindre le relais
def toggle_relay():
    current_state = GPIO.input(RELAY_PIN)
    if current_state == GPIO.LOW:
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Allumer le relais (ce qui allumera la LED)
        button.config(text="Éteindre")  # Modifier le texte du bouton
    else:
        GPIO.output(RELAY_PIN, GPIO.LOW)  # Éteindre le relais (ce qui éteindra la LED)
        button.config(text="Allumer")  # Modifier le texte du bouton

# Création de l'interface avec Tkinter
root = Tk()
root.title("Contrôle du relais")

# Bouton d'activation dans l'interface graphique
button = Button(root, text="Allumer", command=toggle_relay, height=2, width=20)
button.pack(pady=20)

# Boucle principale de l'interface graphique
root.mainloop()

# Nettoyage des GPIO à la fin de l'exécution
GPIO.cleanup()

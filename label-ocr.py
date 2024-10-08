import cv2
import numpy as np
from pyzbar.pyzbar import decode
import time

# Dictionnaires de correspondance pour chaque transporteur (début du code)
transporteur_patterns = {
    "DPD": ["10624000"],
    "CHRONOPOST": ["M593"],
    "GLS": ["FR0A59"],
    "COLISSIMO": ["16A5"]
}

# Dictionnaires de correspondance pour les 4 derniers caractères du code-barres
transporteur_end_patterns = {
    "DPD": [],
    "CHRONOPOST": ["056"],
    "GLS": [],
    "COLISSIMO": []
}

# Fonction pour vérifier la présence des valeurs spécifiques dans le code-barres
def identify_transporteur(barcode_text, patterns, end_patterns):
    for transporteur, codes in patterns.items():
        # Vérifier si les débuts du code-barres correspondent
        for code in codes:
            if code in barcode_text:
                return transporteur

    # Vérifier les 3 derniers caractères
    last_car = barcode_text[-3:]  # Prendre les 3 derniers caractères du code-barres
    for transporteur, end_codes in end_patterns.items():
        if last_car in end_codes:
            return transporteur

    return "Inconnu"

# Fonction pour redresser une étiquette inclinée
def deskew_image(image, contour):
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int0(box)

    width = int(rect[1][0])
    height = int(rect[1][1])

    src_pts = box.astype("float32")
    dst_pts = np.array([[0, height - 1],
                        [0, 0],
                        [width - 1, 0],
                        [width - 1, height - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(image, M, (width, height))
    
    return warped

# Fonction pour ajuster le contraste
def adjust_contrast(image, alpha):
    # Ajuster le contraste : alpha > 1.0 augmente le contraste, alpha < 1.0 le réduit
    new_image = cv2.convertScaleAbs(image, alpha=alpha, beta=0)
    return new_image

# Fonction pour décoder les codes-barres et encadrer précisément
def decode_and_identify_barcodes(label_roi, frame, x, y, w, h):
    decoded_objects = decode(label_roi)
    if decoded_objects:
        for obj in decoded_objects:
            # Texte du code-barres détecté
            barcode_text = obj.data.decode("utf-8")

            # Identifier le transporteur
            transporteur_detected = identify_transporteur(barcode_text, transporteur_patterns, transporteur_end_patterns)

            # Afficher le texte du code-barres et le transporteur sur l'image principale
            cv2.putText(frame, f"Code-barres: {barcode_text}", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Transporteur: {transporteur_detected}", (x, y + h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    else:
        # Si aucun code-barres n'a été détecté
        cv2.putText(frame, "Code-barres non détecté", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

# Capture vidéo
cap = cv2.VideoCapture(0)

# Variables pour calcul des FPS et contraste
prev_time = 0
fps = 0
alpha = 1.0  # Contraste par défaut, peut être ajusté (1.0 = normal, >1.0 = plus de contraste, <1.0 = moins)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Ajuster le contraste de l'image
    frame = adjust_contrast(frame, alpha)

    # Calcul des FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    # Afficher les FPS en haut à gauche
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    # Convertir en niveaux de gris
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Appliquer un flou pour réduire le bruit
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)

    # Appliquer un filtre de luminosité pour atténuer les reflets
    _, thresh = cv2.threshold(blurred, 130, 255, cv2.THRESH_BINARY)

    # Trouver les contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Filtrer par surface et approximations rectangulaires
        area = cv2.contourArea(contour)
        approx = cv2.approxPolyDP(contour, 0.05 * cv2.arcLength(contour, True), True)

        # Se concentrer sur les zones rectangulaires (4 côtés) et une surface minimum
        if len(approx) == 4 and area > 10000:
            x, y, w, h = cv2.boundingRect(approx)

            # Calculer le ratio largeur/hauteur
            aspect_ratio = float(w) / h

            # Vérifier le rapport largeur/hauteur pour éliminer les formes non étiquettes
            if 0.6 < aspect_ratio < 1.6:  # Rectangles proches d'un carré
                # Redresser l'étiquette
                deskewed_label = deskew_image(frame, approx)

                # Dessiner un rectangle autour des étiquettes détectées
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Décoder et afficher les codes-barres à l'intérieur de l'étiquette
                decode_and_identify_barcodes(deskewed_label, frame, x, y, w, h)

                # Ajouter des informations sur la surface et le ratio
                cv2.putText(frame, f"Surface: {int(area)}", (x, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, f"Ratio: {round(aspect_ratio, 2)}", (x, y - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Réduire la taille de la fenêtre vidéo à 50% de l'original
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    small_thresh = cv2.resize(thresh, (0, 0), fx=0.5, fy=0.5)

    # Afficher la vidéo avec les étiquettes et les codes-barres détectés
    cv2.imshow('Detection d\'etiquettes et codes-barres', small_frame)
    cv2.imshow('Threshold Filter', small_thresh)

    # Ajuster le contraste en appuyant sur les touches 'up' et 'down'
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('w'):  # Augmenter le contraste
        alpha += 0.1
    elif key == ord('s'):  # Réduire le contraste
        alpha -= 0.1

cap.release()
cv2.destroyAllWindows()

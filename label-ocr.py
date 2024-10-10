# -*- coding: utf-8 -*-

import cv2
import numpy as np
import time

cap = cv2.VideoCapture(0)

prev_frame_time = 0
new_frame_time = 0

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
middle_line_x = frame_width // 2

transfert_delay = 3

transfer_on_time = 0
transfer_active = False

while True:
    ret, frame = cap.read()
    
    if not ret:
        break

    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
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

    cv2.imshow('Detection d\'etiquettes', frame)
    cv2.imshow('Threshold Filter', thresh)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

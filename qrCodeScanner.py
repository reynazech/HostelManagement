import cv2


video = cv2.VideoCapture(0)
success, frame = video.read()
detector = cv2.QRCodeDetector()


while success:
    hostel_id , coords, pixels = detector.detectAndDecode(frame)

    cv2.imshow('frame', frame)

    print(hostel_id)

    if cv2.waitKey(1) == ord('q'):
        break

    success, frame = video.read()


video.release()
cv2.destroyAllWindows()

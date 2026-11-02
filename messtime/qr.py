"""QR code generation and webcam scanning.

Each student's QR code holds only their student ID; everything else is looked
up in the database, so codes stay valid if a student's details change.
"""

import re
from collections.abc import Callable
from pathlib import Path

DEFAULT_QR_DIR = Path("qr_codes")


def make_qr(student_id: str, out_dir: Path = DEFAULT_QR_DIR) -> Path:
    import segno

    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", student_id)
    path = out_dir / f"{safe_name}.png"
    segno.make_qr(student_id).save(path, scale=8, border=4)
    return path


def scan(on_code: Callable[[str], str], camera: int = 0) -> None:
    """Show the webcam feed and call ``on_code`` for each newly seen QR code.

    ``on_code`` returns a status message that is drawn on the video feed.
    Press ``q`` in the video window to stop.
    """
    import cv2

    video = cv2.VideoCapture(camera)
    if not video.isOpened():
        raise RuntimeError(f"Could not open camera {camera}")

    detector = cv2.QRCodeDetector()
    last_code = None
    message = "Show a QR code to the camera (q to quit)"
    try:
        while True:
            ok, frame = video.read()
            if not ok:
                break

            code, _, _ = detector.detectAndDecode(frame)
            # Only react when a new code appears, so holding a code up doesn't spam scans.
            if code and code != last_code:
                message = on_code(code)
            last_code = code or None

            cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("MessTime scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        video.release()
        cv2.destroyAllWindows()

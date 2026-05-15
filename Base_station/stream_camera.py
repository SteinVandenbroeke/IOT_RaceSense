import cv2
from flask import Flask, Response

app = Flask(__name__)

# The native Coral Camera is typically on /dev/video1.
# If you get a blank feed, try changing this '1' to a '0'.
camera = cv2.VideoCapture(1)

# Set the resolution (adjust if you need a different size)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 320)


def generate_frames():
    while True:
        # Read the camera frame
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode the frame into JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame in a format suitable for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def video_feed():
    # Return the multipart response to stream the video
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    print("Starting raw camera stream server...")
    app.run(host='0.0.0.0', port=5000, debug=False)
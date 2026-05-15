import cv2
from flask import Flask, Response

app = Flask(__name__)

# Force V4L2 backend
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

# Force the specific format the native Coral camera requires
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 320)


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            # This will print in your terminal if the camera is failing
            print("ERROR: Failed to grab frame from camera!")
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# We moved the stream to a specific URL path
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Now the main URL returns a proper webpage with the video embedded inside it
@app.route('/')
def index():
    return '''
    <html>
      <head>
        <title>Coral Camera Stream</title>
        <style>
          body { font-family: sans-serif; text-align: center; background: #222; color: #fff; margin-top: 50px;}
          img { border: 5px solid #fff; border-radius: 8px; }
        </style>
      </head>
      <body>
        <h1>Coral Dev Board Camera Feed</h1>
        <!-- This image tag is what pulls in the video stream -->
        <img src="/video_feed" width="640" height="480" alt="Video feed loading..." />
      </body>
    </html>
    '''


if __name__ == "__main__":
    print("Starting raw camera stream server...")
    app.run(host='0.0.0.0', port=5000, debug=False)
import cv2
from flask import Flask, Response

app = Flask(__name__)

# This is the magic string. It tells GStreamer to grab the camera,
# set the exact resolution/framerate we saw in your terminal,
# and convert it into a format OpenCV understands.
gstreamer_pipeline = (
    "v4l2src device=/dev/video0 ! "
    "video/x-raw,width=640,height=480,framerate=30/1 ! "
    "videoconvert ! "
    "video/x-raw,format=BGR ! "
    "appsink drop=1"
)

# We pass the pipeline string and explicitly tell OpenCV to use the GStreamer backend
camera = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            print("ERROR: OpenCV could not read from the GStreamer pipeline!")
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


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
        <img src="/video_feed" width="640" height="480" alt="Video feed loading..." />
      </body>
    </html>
    '''


if __name__ == "__main__":
    print("Starting GStreamer-powered camera stream server...")
    app.run(host='0.0.0.0', port=5000, debug=False)
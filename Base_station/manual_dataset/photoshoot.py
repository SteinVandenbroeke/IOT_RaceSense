from flask import Flask, Response, render_template_string, jsonify
import cv2
import os
import threading

app = Flask(__name__)

# Define the folder (map) where images will be saved
SAVE_FOLDER = "captured_images"
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

# Initialize camera using your specific hardware configuration
camera = cv2.VideoCapture(1, cv2.CAP_V4L2)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Globals for thread-safe image saving
latest_frame = None
frame_lock = threading.Lock()
img_counter = 1


def generate_frames():
    """Generator function that grabs frames and yields them as a web stream."""
    global latest_frame
    while True:
        success, frame = camera.read()
        if not success:
            break

        # Save a copy of the current frame safely so the /capture route can grab it
        with frame_lock:
            latest_frame = frame.copy()

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield the frame in the byte format expected by the browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def index():
    # A simple, self-contained HTML page
    html = """
    <html>
    <head>
        <title>Coral Camera Stream</title>
        <style>
            body { text-align: center; font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; }
            img { max-width: 100%; border: 3px solid #333; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
            .btn { margin-top: 20px; padding: 15px 30px; font-size: 20px; font-weight: bold; color: white; background-color: #007bff; border: none; border-radius: 5px; cursor: pointer; transition: 0.2s; }
            .btn:hover { background-color: #0056b3; }
            #status { margin-top: 15px; font-size: 18px; color: #28a745; font-weight: bold; height: 25px; }
        </style>
        <script>
            // Function to hit our API and tell Python to save the image
            function captureImage() {
                fetch('/capture', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        const statusEl = document.getElementById('status');
                        statusEl.innerText = data.message;
                        // Clear the success message after 3 seconds
                        setTimeout(() => statusEl.innerText = '', 3000);
                    })
                    .catch(err => console.error(err));
            }

            // Listen for the Space bar being pressed
            document.addEventListener('keydown', function(event) {
                if (event.code === 'Space') {
                    event.preventDefault(); // Stop the page from scrolling down
                    captureImage();
                }
            });
        </script>
    </head>
    <body>
        <h1>Coral Live Camera Feed</h1>
        <img src="/video_feed" alt="Live Stream is loading..." />
        <br>
        <button class="btn" onclick="captureImage()">📸 Capture Image (or press Space)</button>
        <div id="status"></div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/video_feed')
def video_feed():
    # Standard multipart response for video streaming
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/capture', methods=['POST'])
def capture():
    """API endpoint triggered by the web page to save the current frame."""
    global img_counter, latest_frame

    with frame_lock:
        if latest_frame is not None:
            # Create the file name (e.g., captured_images/image_1.jpg)
            img_name = os.path.join(SAVE_FOLDER, f"image_{img_counter}.jpg")

            # Save the frame on the Coral board
            cv2.imwrite(img_name, latest_frame)
            print(f"Captured: {img_name}")

            img_counter += 1
            return jsonify({"status": "success", "message": f"Saved {img_name} successfully!"}), 200
        else:
            return jsonify({"status": "error", "message": "Camera not ready yet!"}), 500


if __name__ == "__main__":
    print("\nStarting Web Server...")
    print("Open a web browser on your computer and go to: http://<your-coral-board-ip>:5000")
    # host='0.0.0.0' makes the server accessible to other devices on your network
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
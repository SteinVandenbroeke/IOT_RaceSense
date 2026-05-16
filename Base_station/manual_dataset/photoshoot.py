import cv2
import os

SAVE_FOLDER = "captured_images"

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)


def main():
    print("Initializing Camera...")

    camera = cv2.VideoCapture(1, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    img_counter = 1

    print("Camera started successfully in HEADLESS mode!")

    while True:
        # Using standard terminal input instead of OpenCV's GUI key listener
        cmd = input(f"[{img_counter}] Press ENTER to snap a photo, or type 'q' and ENTER to quit: ")

        if cmd.strip().lower() == 'q':
            print("Exiting...")
            break

        # Flush the camera buffer to ensure we get a fresh frame
        # (Since input() pauses the script, old frames pile up in the buffer)
        for _ in range(5):
            camera.grab()

        success, frame = camera.read()

        if not success:
            print("Failed to grab frame.")
            break

        # Save the image
        img_name = os.path.join(SAVE_FOLDER, f"image_{img_counter}.jpg")
        cv2.imwrite(img_name, frame)
        print(f" -> Saved {img_name} successfully!\n")

        img_counter += 1

    camera.release()


if __name__ == "__main__":
    main()
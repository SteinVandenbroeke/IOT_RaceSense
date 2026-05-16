import cv2
import os

# Define the folder (map) where images will be saved
SAVE_FOLDER = "captured_images"

# Create the folder if it doesn't exist already
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)


def main():
    print("Initializing Camera...")

    # Using the exact camera setup from your main.py file
    camera = cv2.VideoCapture(1, cv2.CAP_V4L2)

    # Setting the resolution to match your configuration
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not camera.isOpened():
        print("Error: Could not open camera. Check your hardware connection.")
        return

    # Counter to give each image a unique, incrementing name
    img_counter = 1

    print("Camera started successfully!")
    print(" -> Press 'SPACE' to take a picture.")
    print(" -> Press 'ESC' or 'q' to exit the program.")

    while True:
        # Grab a frame from the camera
        success, frame = camera.read()

        if not success:
            print("Failed to grab frame.")
            break

        # Show the live feed in a window so you can frame your shot
        cv2.imshow("Live Camera Feed", frame)

        # Wait for a key press for 1 millisecond
        key = cv2.waitKey(1) & 0xFF

        # If the 'ESC' key (ASCII 27) or 'q' is pressed, exit the loop
        if key == 27 or key == ord('q'):
            print("Exiting...")
            break

        # If the 'SPACE' key (ASCII 32) is pressed, save the image
        elif key == 32:
            # Create the file path (e.g., captured_images/image_1.jpg)
            img_name = os.path.join(SAVE_FOLDER, f"image_{img_counter}.jpg")

            # Save the frame to the file
            cv2.imwrite(img_name, frame)
            print(f"[{img_counter}] Saved {img_name} successfully!")

            # Increase the counter for the next picture
            img_counter += 1

    # Cleanup: release the camera hardware and close the preview window
    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
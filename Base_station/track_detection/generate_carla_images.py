import carla
import random
import os
import queue
import numpy as np
import cv2

# Create directories to store the output images and segmentation masks
os.makedirs('output_track_topdown/rgb', exist_ok=True)
os.makedirs('output_track_topdown/masks', exist_ok=True)

# ---------------------------------------------------------------------------
# Setup: Parameters
# ---------------------------------------------------------------------------
IMAGES_PER_WEATHER = 50
CAMERA_HEIGHT = 17.0
PITCH_ANGLE = -90.0

# --- SET YOUR ROAD CLASS ID HERE ---
# Standard CARLA is 7. Based on your debug, it's likely 24 or 28.
ROAD_CLASS = [1,24]

WEATHERS = {
    'ClearNoon': carla.WeatherParameters.ClearNoon,
    'HardRain': carla.WeatherParameters.HardRainNoon,
    'ClearSunset': carla.WeatherParameters.ClearSunset,
    'Night': carla.WeatherParameters.HardRainNight
}


def main():
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.load_world('Town04')

    original_settings = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    actor_list = []

    try:
        blueprint_library = world.get_blueprint_library()
        world_map = world.get_map()

        image_w = 800
        image_h = 600
        cam_fov = 90.0

        # 1. Spawn RGB Camera
        rgb_bp = blueprint_library.find('sensor.camera.rgb')
        rgb_bp.set_attribute('image_size_x', str(image_w))
        rgb_bp.set_attribute('image_size_y', str(image_h))
        rgb_bp.set_attribute('fov', str(cam_fov))
        rgb_camera = world.spawn_actor(rgb_bp, carla.Transform())
        actor_list.append(rgb_camera)

        # 2. Spawn Semantic Segmentation Camera
        seg_bp = blueprint_library.find('sensor.camera.semantic_segmentation')
        seg_bp.set_attribute('image_size_x', str(image_w))
        seg_bp.set_attribute('image_size_y', str(image_h))
        seg_bp.set_attribute('fov', str(cam_fov))
        seg_camera = world.spawn_actor(seg_bp, carla.Transform())
        actor_list.append(seg_camera)

        # 3. Setup Queues
        image_queue_rgb = queue.Queue()
        image_queue_seg = queue.Queue()

        rgb_camera.listen(image_queue_rgb.put)
        seg_camera.listen(image_queue_seg.put)

        all_waypoints = world_map.generate_waypoints(distance=15.0)

        # ------------------------------------------------------------------
        # MASTER LOOP
        # ------------------------------------------------------------------
        for weather_name, weather_params in WEATHERS.items():
            print(f"\n--- Setting Weather: {weather_name} ---")
            world.set_weather(weather_params)

            for _ in range(10):
                world.tick()
                _ = image_queue_rgb.get()
                _ = image_queue_seg.get()

            sampled_waypoints = random.sample(all_waypoints, IMAGES_PER_WEATHER)

            for i, waypoint in enumerate(sampled_waypoints):
                cam_transform = waypoint.transform
                cam_transform.location.z += CAMERA_HEIGHT
                cam_transform.rotation.pitch = PITCH_ANGLE

                rgb_camera.set_transform(cam_transform)
                seg_camera.set_transform(cam_transform)
                world.tick()

                rgb_image = image_queue_rgb.get()
                seg_image = image_queue_seg.get()

                file_name = f"{weather_name}_loc{i:03d}_{rgb_image.frame}"
                rgb_path = f"output_track_topdown/rgb/{file_name}.png"
                seg_path = f"output_track_topdown/masks/{file_name}.png"

                rgb_image.save_to_disk(rgb_path)

                # --- PROCESS SEGMENTATION MASK ---
                seg_data = np.frombuffer(seg_image.raw_data, dtype=np.uint8)
                seg_data = np.reshape(seg_data, (image_h, image_w, 4))

                # Extract the Red channel where CARLA stores the ID
                red_channel = seg_data[:, :, 2]

                # Create a binary mask directly from the ROAD_CLASS ID
                road_mask = np.where(np.isin(red_channel, ROAD_CLASS), 255, 0).astype(np.uint8)

                # Save the processed pure black & white mask
                cv2.imwrite(seg_path, road_mask)

                if i % 10 == 0:
                    print(f"Captured {i}/{IMAGES_PER_WEATHER} images for {weather_name}")

        rgb_camera.stop()
        seg_camera.stop()

    finally:
        world.apply_settings(original_settings)
        for actor in reversed(actor_list):
            if actor.is_alive:
                actor.destroy()
        print("\nDataset generation complete.")


if __name__ == '__main__':
    main()
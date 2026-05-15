import carla
import random
import os
import queue
import numpy as np
import cv2

# Create directories to store the output images and segmentation masks
os.makedirs('output_line_topdown/rgb', exist_ok=True)
os.makedirs('output_line_topdown/masks', exist_ok=True)

# ---------------------------------------------------------------------------
# Setup: Parameters
# ---------------------------------------------------------------------------
IMAGES_PER_WEATHER = 50
CAMERA_HEIGHT = 17.0
PITCH_ANGLE = -90.0

# --- SET YOUR ROAD CLASS ID HERE ---
# Standard CARLA is 7. Based on your debug, it's likely 24 or 28.
ROAD_CLASS = [24]

WEATHERS = {
    'ClearNoon': carla.WeatherParameters.ClearNoon,
    'HardRain': carla.WeatherParameters.HardRainNoon,
    'ClearSunset': carla.WeatherParameters.ClearSunset,
    'Night': carla.WeatherParameters.HardRainNight
}


def is_sharp_turn(waypoint, lookahead_distance=15.0, min_angle=20.0):
    """
    Checks if the road curves by at least `min_angle` degrees over `lookahead_distance`.
    Excludes any turns that occur inside intersections.
    """
    # 1. Reject if the current waypoint is inside an intersection
    if waypoint.is_junction:
        return False

    next_wps = waypoint.next(lookahead_distance)
    if not next_wps:
        return False  # Dead end or intersection loss

    future_wp = next_wps[0]

    # 2. Reject if the turn leads directly into an intersection
    if future_wp.is_junction:
        return False

    yaw_current = waypoint.transform.rotation.yaw
    yaw_future = future_wp.transform.rotation.yaw

    # Calculate shortest angular difference
    diff = abs(yaw_future - yaw_current) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff

    return diff >= min_angle


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

        raw_waypoints = world_map.generate_waypoints(distance=15.0)
        all_waypoints = [wp for wp in raw_waypoints if is_sharp_turn(wp, lookahead_distance=15.0, min_angle=20.0)]
        print(f"Found {len(all_waypoints)} waypoints that match the 20-degree turn criteria.")

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

            # Safely sample depending on how many waypoints survived the filter
            sample_size = min(IMAGES_PER_WEATHER, len(all_waypoints))
            if sample_size < IMAGES_PER_WEATHER:
                print(f"Warning: Only {sample_size} valid turn waypoints available for {weather_name}.")

            sampled_waypoints = random.sample(all_waypoints, sample_size)

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
                rgb_path = f"output_line_topdown/rgb/{file_name}.png"
                seg_path = f"output_line_topdown/masks/{file_name}.png"

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
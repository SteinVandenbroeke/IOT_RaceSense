import carla
import random
import os
import queue
import numpy as np
import cv2

# Create directories to store the output images and segmentation masks
os.makedirs('output_car/rgb', exist_ok=True)
os.makedirs('output_car/masks', exist_ok=True)

# ---------------------------------------------------------------------------
# Setup: Parameters
# ---------------------------------------------------------------------------
TURN_IMAGES_PER_WEATHER = 20
RANDOM_IMAGES_PER_WEATHER = 50
CAMERA_HEIGHT = 17.0
PITCH_ANGLE = -90.0

# --- FIXED: SET TO 10 FOR VEHICLES ---
CAR_CLASS = [14]

WEATHERS = {
    'ClearNoon': carla.WeatherParameters.ClearNoon,
    'HardRain': carla.WeatherParameters.HardRainNoon,
    'ClearSunset': carla.WeatherParameters.ClearSunset,
    # 'Night': carla.WeatherParameters.HardRainNight
}


def is_sharp_turn(waypoint, lookahead_distance=15.0, min_angle=20.0):
    if waypoint.is_junction:
        return False
    next_wps = waypoint.next(lookahead_distance)
    if not next_wps:
        return False
    future_wp = next_wps[0]
    if future_wp.is_junction:
        return False

    yaw_current = waypoint.transform.rotation.yaw
    yaw_future = future_wp.transform.rotation.yaw
    diff = abs(yaw_future - yaw_current) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff >= min_angle


def is_narrow_road(waypoint):
    if waypoint.lane_type != carla.LaneType.Driving:
        return False
    right_wp = waypoint.get_right_lane()
    left_wp = waypoint.get_left_lane()
    if right_wp and right_wp.lane_type == carla.LaneType.Driving:
        if (waypoint.lane_id * right_wp.lane_id) > 0:
            return False
    if left_wp and left_wp.lane_type == carla.LaneType.Driving:
        if (waypoint.lane_id * left_wp.lane_id) > 0:
            return False
    return True


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
    car_pool = []

    try:
        blueprint_library = world.get_blueprint_library()
        world_map = world.get_map()

        # ---------------------------------------------------
        # PREPARE TO REMOVE OVERLAPPING OBJECTS
        # ---------------------------------------------------
        labels_to_hide = [
            carla.CityObjectLabel.Vegetation,
            carla.CityObjectLabel.TrafficSigns,
            carla.CityObjectLabel.Poles,
            carla.CityObjectLabel.Buildings,
            carla.CityObjectLabel.Sidewalks,
            carla.CityObjectLabel.TrafficLight,
            carla.CityObjectLabel.Roads,
            carla.CityObjectLabel.RoadLines,
            carla.CityObjectLabel.Bus,
            carla.CityObjectLabel.Fences,
            carla.CityObjectLabel.Other,
            carla.CityObjectLabel.Bicycle,
        ]

        hidden_ids = []
        for label in labels_to_hide:
            env_objects = world.get_environment_objects(label)
            hidden_ids.extend([obj.id for obj in env_objects])

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

        # ---------------------------------------------------
        # 4. SPAWN THE VEHICLE POOL
        # ---------------------------------------------------
        vehicle_bps = blueprint_library.filter('vehicle.*')

        # Filter out bicycles/motorcycles to ensure we only get cars
        car_bps = [bp for bp in vehicle_bps if int(bp.get_attribute('number_of_wheels').as_int()) >= 4]

        # Pick 20 unique random cars for a larger variety pool
        chosen_bps = random.sample(car_bps, min(20, len(car_bps)))

        for i, bp in enumerate(chosen_bps):
            # FIXED: Space out the cars vertically so their collision boxes don't overlap on spawn!
            # Car 1 is at Z=100, Car 2 at Z=110, Car 3 at Z=120, etc.
            hide_transform = carla.Transform(carla.Location(0, 0, 100 + (i * 10)))

            # Randomize the color of the car for even more variety
            if bp.has_attribute('color'):
                color = random.choice(bp.get_attribute('color').recommended_values)
                bp.set_attribute('color', color)

            try:
                car = world.spawn_actor(bp, hide_transform)
                car.set_simulate_physics(False)
                car_pool.append(car)
                actor_list.append(car)
            except Exception as e:
                print(f"Failed to spawn a vehicle: {e}")

        # Base hide transform to use when moving cars OUT of the frame later
        general_hide_transform = carla.Transform(carla.Location(0, 0, 500))

        # Generate all waypoints
        all_waypoints = world_map.generate_waypoints(distance=15.0)

        # Filter waypoints
        narrow_waypoints = [wp for wp in all_waypoints if is_narrow_road(wp)]
        turn_waypoints = [wp for wp in narrow_waypoints if is_sharp_turn(wp, lookahead_distance=15.0, min_angle=20.0)]
        random_waypoints = [wp for wp in narrow_waypoints if wp not in turn_waypoints]

        print(
            f"Found {len(turn_waypoints)} narrow turn waypoints and {len(random_waypoints)} narrow straight waypoints.")
        print(f"Successfully loaded {len(car_pool)} distinct vehicles into the pool.")

        # ------------------------------------------------------------------
        # MASTER LOOP (TWO-PASS ARCHITECTURE)
        # ------------------------------------------------------------------
        for weather_name, weather_params in WEATHERS.items():
            print(f"\n--- Setting Weather: {weather_name} ---")
            world.set_weather(weather_params)

            for _ in range(10):
                world.tick()
                _ = image_queue_rgb.get()
                _ = image_queue_seg.get()

            t_sample_size = min(TURN_IMAGES_PER_WEATHER, len(turn_waypoints))
            r_sample_size = min(RANDOM_IMAGES_PER_WEATHER, len(random_waypoints))

            sampled_turns = random.sample(turn_waypoints, t_sample_size)
            sampled_randoms = random.sample(random_waypoints, r_sample_size)

            capture_targets = [("turn", wp) for wp in sampled_turns] + [("random", wp) for wp in sampled_randoms]
            random.shuffle(capture_targets)

            # Pre-calculate the specific car and offset for EVERY image in this weather batch
            # This ensures Pass 1 and Pass 2 use the exact same layout
            frame_configs = []
            for wp_type, wp in capture_targets:
                chosen_car = random.choice(car_pool)
                # Random longitudinal (forward/backward) offset
                offset_x = random.uniform(-3.0, 3.0)
                # Random lateral (left/right) offset
                offset_y = random.uniform(-1.5, 1.5)
                # Slight random yaw rotation
                offset_yaw = random.uniform(-15.0, 15.0)
                frame_configs.append((wp_type, wp, chosen_car, offset_x, offset_y, offset_yaw))

            # ==========================================
            # PASS 1: FULL WORLD (Capture RGB)
            # ==========================================
            print(f"Pass 1: Capturing full world RGB images for {weather_name}...")
            for i, (wp_type, waypoint, chosen_car, ox, oy, oyaw) in enumerate(frame_configs):

                # Hide all cars
                for c in car_pool:
                    c.set_transform(general_hide_transform)

                # Calculate offset transform for chosen car
                fw = waypoint.transform.get_forward_vector()
                rt = waypoint.transform.get_right_vector()
                loc = waypoint.transform.location

                car_x = loc.x + fw.x * ox + rt.x * oy
                car_y = loc.y + fw.y * ox + rt.y * oy
                car_z = loc.z + 0.1
                car_yaw = waypoint.transform.rotation.yaw + oyaw

                car_transform = carla.Transform(
                    carla.Location(car_x, car_y, car_z),
                    carla.Rotation(pitch=waypoint.transform.rotation.pitch, yaw=car_yaw,
                                   roll=waypoint.transform.rotation.roll)
                )
                chosen_car.set_transform(car_transform)

                # Teleport Camera to stay centered on the waypoint
                cam_transform = carla.Transform(
                    carla.Location(loc.x, loc.y, loc.z + CAMERA_HEIGHT),
                    carla.Rotation(pitch=PITCH_ANGLE, yaw=waypoint.transform.rotation.yaw,
                                   roll=waypoint.transform.rotation.roll)
                )
                rgb_camera.set_transform(cam_transform)
                seg_camera.set_transform(cam_transform)

                world.tick()

                rgb_image = image_queue_rgb.get()
                _ = image_queue_seg.get()

                file_name = f"{weather_name}_{wp_type}_loc{i:03d}"
                rgb_path = f"output_car/rgb/{file_name}.png"
                rgb_image.save_to_disk(rgb_path)

            # ==========================================
            # TRANSITION: HIDE OVERLAPPING OBJECTS
            # ==========================================
            world.enable_environment_objects(hidden_ids, False)

            for _ in range(5):
                world.tick()
                _ = image_queue_rgb.get()
                _ = image_queue_seg.get()

            # ==========================================
            # PASS 2: BARE WORLD (Capture Mask)
            # ==========================================
            print(f"Pass 2: Capturing unobstructed segmentation masks for {weather_name}...")
            for i, (wp_type, waypoint, chosen_car, ox, oy, oyaw) in enumerate(frame_configs):

                # Hide all cars
                for c in car_pool:
                    c.set_transform(general_hide_transform)

                # Reapply exact same offset transform
                fw = waypoint.transform.get_forward_vector()
                rt = waypoint.transform.get_right_vector()
                loc = waypoint.transform.location

                car_x = loc.x + fw.x * ox + rt.x * oy
                car_y = loc.y + fw.y * ox + rt.y * oy
                car_z = loc.z + 0.1
                car_yaw = waypoint.transform.rotation.yaw + oyaw

                car_transform = carla.Transform(
                    carla.Location(car_x, car_y, car_z),
                    carla.Rotation(pitch=waypoint.transform.rotation.pitch, yaw=car_yaw,
                                   roll=waypoint.transform.rotation.roll)
                )
                chosen_car.set_transform(car_transform)

                # Teleport Camera to stay centered on the waypoint
                cam_transform = carla.Transform(
                    carla.Location(loc.x, loc.y, loc.z + CAMERA_HEIGHT),
                    carla.Rotation(pitch=PITCH_ANGLE, yaw=waypoint.transform.rotation.yaw,
                                   roll=waypoint.transform.rotation.roll)
                )
                rgb_camera.set_transform(cam_transform)
                seg_camera.set_transform(cam_transform)

                world.tick()

                _ = image_queue_rgb.get()
                seg_image = image_queue_seg.get()

                file_name = f"{weather_name}_{wp_type}_loc{i:03d}"
                seg_path = f"output_car/masks/{file_name}.png"

                # Process Mask
                seg_data = np.frombuffer(seg_image.raw_data, dtype=np.uint8)
                seg_data = np.reshape(seg_data, (image_h, image_w, 4))
                red_channel = seg_data[:, :, 2]

                car_mask = np.where(np.isin(red_channel, CAR_CLASS), 255, 0).astype(np.uint8)
                cv2.imwrite(seg_path, car_mask)

            # ==========================================
            # CLEANUP: RESTORE WORLD FOR NEXT WEATHER
            # ==========================================
            world.enable_environment_objects(hidden_ids, True)

            for _ in range(5):
                world.tick()
                _ = image_queue_rgb.get()
                _ = image_queue_seg.get()

            print(f"Finished {weather_name} batch.")

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
import carla
import random
import numpy as np
import cv2
import os

# Create directories to store the output images
os.makedirs('output/rgb', exist_ok=True)
os.makedirs('output/mask', exist_ok=True)

# ---------------------------------------------------------------------------
# Setup: Scenes, Weather, and Vehicles
# ---------------------------------------------------------------------------
TARGET_FRAMES = 84
WARMUP_TICKS = 20
TARGET_SPEED_KPH = 30.0

SCENES = [
    {
        'name': 'Angled_Street',
        'loc': carla.Location(x=217, y=-135, z=17),
        'rot': carla.Rotation(pitch=-90.0, yaw=40.0, roll=0.0)
    },
    {
        'name': 'High_Curve',
        'loc': carla.Location(x=210, y=-135, z=17),
        'rot': carla.Rotation(pitch=-90.0, yaw=50.7, roll=0.0)
    }
]

WEATHERS = {
    'ClearNoon': carla.WeatherParameters.ClearNoon,
    'HardRain': carla.WeatherParameters.HardRainNoon,
    'ClearSunset': carla.WeatherParameters.ClearSunset,
    'Night': carla.WeatherParameters.HardRainNight
}

VEHICLE_MODELS = [
    'vehicle.ford.mustang',
    'vehicle.audi.tt',
    'vehicle.tesla.model3',
    'vehicle.lincoln.mkz_2020',
    'vehicle.nissan.patrol_2021',
]


def process_mask(image, target_vehicle_id, prefix):
    image_data = np.frombuffer(image.raw_data, dtype=np.uint8)
    image_data = np.reshape(image_data, (image.height, image.width, 4))

    b = image_data[:, :, 0].astype(np.uint32)
    g = image_data[:, :, 1].astype(np.uint32)
    instance_ids = g + (b << 8)

    mask = np.zeros((image.height, image.width), dtype=np.uint8)
    mask[instance_ids == target_vehicle_id] = 255

    cv2.imwrite(f'output/mask/{prefix}_mask_{image.frame}.png', mask)


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
        tm_port = 8050
        tm = client.get_trafficmanager(tm_port)
        tm.set_synchronous_mode(True)

        # Spawn Cameras once, we will move them later
        rgb_bp = blueprint_library.find('sensor.camera.rgb')
        rgb_bp.set_attribute('image_size_x', '800')
        rgb_bp.set_attribute('image_size_y', '600')
        rgb_camera = world.spawn_actor(rgb_bp, carla.Transform())
        actor_list.append(rgb_camera)

        inst_bp = blueprint_library.find('sensor.camera.instance_segmentation')
        inst_bp.set_attribute('image_size_x', '800')
        inst_bp.set_attribute('image_size_y', '600')
        inst_camera = world.spawn_actor(inst_bp, carla.Transform())
        actor_list.append(inst_camera)

        # ------------------------------------------------------------------
        # MASTER LOOP: Scene -> Weather -> Vehicle
        # ------------------------------------------------------------------
        for scene in SCENES:
            print(f"\n{'#' * 50}\nMoving to Scene: {scene['name']}\n{'#' * 50}")

            # Move cameras to the new scene location
            new_cam_transform = carla.Transform(scene['loc'], scene['rot'])
            rgb_camera.set_transform(new_cam_transform)
            inst_camera.set_transform(new_cam_transform)

            for weather_name, weather_params in WEATHERS.items():
                print(f"\n--- Setting Weather: {weather_name} ---")
                world.set_weather(weather_params)

                for model_name in VEHICLE_MODELS:
                    car_nickname = model_name.split('.')[-1]
                    file_prefix = f"{scene['name']}_{weather_name}_{car_nickname}"

                    vehicle_bp = blueprint_library.find(model_name)

                    # Randomize vehicle color!
                    if vehicle_bp.has_attribute('color'):
                        color = random.choice(vehicle_bp.get_attribute('color').recommended_values)
                        vehicle_bp.set_attribute('color', color)

                    # Spawn logic
                    base_waypoint = world_map.get_waypoint(scene['loc'])
                    previous_waypoints = base_waypoint.previous(20.0)
                    spawn_waypoint = previous_waypoints[0] if previous_waypoints else base_waypoint

                    spawn_transform = spawn_waypoint.transform
                    spawn_transform.location.z += 0.5

                    vehicle = world.spawn_actor(vehicle_bp, spawn_transform)
                    target_id = vehicle.id

                    vehicle.set_autopilot(True, tm_port)
                    tm.ignore_lights_percentage(vehicle, 100)
                    tm.ignore_signs_percentage(vehicle, 100)
                    tm.ignore_vehicles_percentage(vehicle, 100)
                    tm.auto_lane_change(vehicle, False)

                    # Warm-up 1
                    for _ in range(WARMUP_TICKS):
                        world.tick()

                    # RUN 1 (Forward)
                    rgb_camera.listen(
                        lambda image, p=file_prefix: image.save_to_disk(f'output/rgb/{p}_FWD_{image.frame}.png'))
                    inst_camera.listen(lambda image, tid=target_id, p=file_prefix: process_mask(image, tid, f"{p}_FWD"))

                    speed_m_s = TARGET_SPEED_KPH / 3.6
                    for _ in range(TARGET_FRAMES):
                        forward_vec = vehicle.get_transform().get_forward_vector()
                        vehicle.set_target_velocity(carla.Vector3D(forward_vec.x * speed_m_s, forward_vec.y * speed_m_s,
                                                                   forward_vec.z * speed_m_s))
                        world.tick()

                    rgb_camera.stop()
                    inst_camera.stop()

                    # Reposition to Opposite Lane
                    current_waypoint = world_map.get_waypoint(vehicle.get_location())
                    opposite_waypoint = current_waypoint

                    while opposite_waypoint is not None:
                        if opposite_waypoint.lane_id * current_waypoint.lane_id < 0:
                            break
                        opposite_waypoint = opposite_waypoint.get_left_lane()

                    if opposite_waypoint:
                        new_transform = opposite_waypoint.transform
                    else:
                        new_transform = vehicle.get_transform()
                        new_transform.rotation.yaw += 180.0

                    new_transform.location.z += 0.5
                    vehicle.set_transform(new_transform)

                    # Warm-up 2
                    for _ in range(WARMUP_TICKS):
                        world.tick()

                    # RUN 2 (Backward)
                    rgb_camera.listen(
                        lambda image, p=file_prefix: image.save_to_disk(f'output/rgb/{p}_BWD_{image.frame}.png'))
                    inst_camera.listen(lambda image, tid=target_id, p=file_prefix: process_mask(image, tid, f"{p}_BWD"))

                    for _ in range(TARGET_FRAMES):
                        forward_vec = vehicle.get_transform().get_forward_vector()
                        vehicle.set_target_velocity(carla.Vector3D(forward_vec.x * speed_m_s, forward_vec.y * speed_m_s,
                                                                   forward_vec.z * speed_m_s))
                        world.tick()

                    rgb_camera.stop()
                    inst_camera.stop()
                    vehicle.destroy()

    finally:
        world.apply_settings(original_settings)
        for actor in reversed(actor_list):
            if actor.is_alive:
                actor.destroy()
        print("Generation complete.")


if __name__ == '__main__':
    main()
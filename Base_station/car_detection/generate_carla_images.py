import carla
import random
import numpy as np
import os
import json

# Create directories to store the output images and keypoints
os.makedirs('output_keypoints/rgb', exist_ok=True)
os.makedirs('output_keypoints/keypoints', exist_ok=True)

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


# ---------------------------------------------------------------------------
# Projection Math Helpers
# ---------------------------------------------------------------------------
def get_camera_intrinsic(w, h, fov):
    focal = w / (2.0 * np.tan(fov * np.pi / 360.0))
    K = np.identity(3)
    K[0, 0] = K[1, 1] = focal
    K[0, 2] = w / 2.0
    K[1, 2] = h / 2.0
    return K


def project_3d_to_2d(world_point, K, world_2_cam):
    # 1. Convert to Homogeneous 3D point and apply World-to-Camera transform
    point = np.array([world_point.x, world_point.y, world_point.z, 1.0])
    point_camera = np.dot(world_2_cam, point)

    # 2. Swap CARLA left-handed coordinates to standard camera right-handed
    # CARLA: X forward, Y right, Z up
    # Camera: X right, Y down, Z forward
    x_c = point_camera[1]
    y_c = -point_camera[2]
    z_c = point_camera[0]

    # 3. Ignore points behind the camera
    if z_c <= 0.0:
        return None

    # 4. Project to 2D using Intrinsic Matrix
    point_2d = np.dot(K, np.array([x_c, y_c, z_c]))
    u = int(point_2d[0] / point_2d[2])
    v = int(point_2d[1] / point_2d[2])

    return [u, v]


def save_keypoints(vehicle, rgb_camera, K, file_path):
    # Get the bounding box vertices in world space
    bbox = vehicle.bounding_box
    vertices = bbox.get_world_vertices(vehicle.get_transform())

    # Get camera extrinsic matrix
    world_2_cam = np.linalg.inv(rgb_camera.get_transform().get_matrix())

    keypoints = []
    for vertex in vertices:
        p2d = project_3d_to_2d(vertex, K, world_2_cam)
        if p2d:
            keypoints.append(p2d)

    with open(file_path, 'w') as f:
        json.dump(keypoints, f)


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

        # Spawn RGB Camera
        image_w = 800
        image_h = 600
        cam_fov = 90.0

        rgb_bp = blueprint_library.find('sensor.camera.rgb')
        rgb_bp.set_attribute('image_size_x', str(image_w))
        rgb_bp.set_attribute('image_size_y', str(image_h))
        rgb_bp.set_attribute('fov', str(cam_fov))
        rgb_camera = world.spawn_actor(rgb_bp, carla.Transform())
        actor_list.append(rgb_camera)

        # Calculate intrinsic matrix once
        K = get_camera_intrinsic(image_w, image_h, cam_fov)

        # ------------------------------------------------------------------
        # MASTER LOOP: Scene -> Weather -> Vehicle
        # ------------------------------------------------------------------
        for scene in SCENES:
            print(f"\n{'#' * 50}\nMoving to Scene: {scene['name']}\n{'#' * 50}")

            new_cam_transform = carla.Transform(scene['loc'], scene['rot'])
            rgb_camera.set_transform(new_cam_transform)

            for weather_name, weather_params in WEATHERS.items():
                print(f"\n--- Setting Weather: {weather_name} ---")
                world.set_weather(weather_params)

                for model_name in VEHICLE_MODELS:
                    car_nickname = model_name.split('.')[-1]
                    file_prefix = f"{scene['name']}_{weather_name}_{car_nickname}"

                    vehicle_bp = blueprint_library.find(model_name)

                    if vehicle_bp.has_attribute('color'):
                        color = random.choice(vehicle_bp.get_attribute('color').recommended_values)
                        vehicle_bp.set_attribute('color', color)

                    base_waypoint = world_map.get_waypoint(scene['loc'])
                    previous_waypoints = base_waypoint.previous(20.0)
                    spawn_waypoint = previous_waypoints[0] if previous_waypoints else base_waypoint

                    spawn_transform = spawn_waypoint.transform
                    spawn_transform.location.z += 0.5

                    vehicle = world.spawn_actor(vehicle_bp, spawn_transform)

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
                        lambda image, p=file_prefix: image.save_to_disk(f'output_keypoints/rgb/{p}_FWD_{image.frame}.png'))

                    speed_m_s = TARGET_SPEED_KPH / 3.6
                    for _ in range(TARGET_FRAMES):
                        forward_vec = vehicle.get_transform().get_forward_vector()
                        vehicle.set_target_velocity(carla.Vector3D(forward_vec.x * speed_m_s, forward_vec.y * speed_m_s,
                                                                   forward_vec.z * speed_m_s))

                        frame_id = world.tick()
                        json_path = f'output_keypoints/keypoints/{file_prefix}_FWD_{frame_id}.json'
                        save_keypoints(vehicle, rgb_camera, K, json_path)

                    rgb_camera.stop()

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
                        lambda image, p=file_prefix: image.save_to_disk(f'output_keypoints/rgb/{p}_BWD_{image.frame}.png'))

                    for _ in range(TARGET_FRAMES):
                        forward_vec = vehicle.get_transform().get_forward_vector()
                        vehicle.set_target_velocity(carla.Vector3D(forward_vec.x * speed_m_s, forward_vec.y * speed_m_s,
                                                                   forward_vec.z * speed_m_s))

                        frame_id = world.tick()
                        json_path = f'output_keypoints/keypoints/{file_prefix}_BWD_{frame_id}.json'
                        save_keypoints(vehicle, rgb_camera, K, json_path)

                    rgb_camera.stop()
                    vehicle.destroy()

    finally:
        world.apply_settings(original_settings)
        for actor in reversed(actor_list):
            if actor.is_alive:
                actor.destroy()
        print("Generation complete.")


if __name__ == '__main__':
    main()
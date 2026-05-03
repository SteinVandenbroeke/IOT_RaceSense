import carla
import os
import queue


def main():
    # 1. Connect to Client and Load Map
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.load_world('Town04')

    # 2. Unload unneeded map layers (Performance Boost)
    # This removes trees, grass, buildings, and parked cars, keeping just the road/infrastructure
    world.unload_map_layer(carla.MapLayer.Foliage)
    world.unload_map_layer(carla.MapLayer.Buildings)
    world.unload_map_layer(carla.MapLayer.ParkedVehicles)

    # Set synchronous mode to ensure perfect frame capture
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)

    os.makedirs('output_print', exist_ok=True)

    # 3. Setup Camera Transform (Lowered Z for zooming in)
    # Changed Z from 17.0 down to 7.0 to get much closer to the ground
    cam_transform = carla.Transform(
        carla.Location(x=210, y=-135, z=7.0),
        carla.Rotation(pitch=-90.0, yaw=50.7, roll=0.0)
    )

    blueprint_library = world.get_blueprint_library()

    # 4. Configure High-Resolution Camera
    rgb_bp = blueprint_library.find('sensor.camera.rgb')
    rgb_bp.set_attribute('image_size_x', '4960')
    rgb_bp.set_attribute('image_size_y', '3508')
    rgb_bp.set_attribute('fov', '60.0')  # Reduced FOV from 90 to 60 for an optical zoom effect

    # Force max crispness by disabling blur effects
    rgb_bp.set_attribute('motion_blur_intensity', '0.0')
    rgb_bp.set_attribute('blur_amount', '0.0')

    # Spawn the camera
    rgb_camera = world.spawn_actor(rgb_bp, cam_transform)

    # Crisp noon lighting for maximum road visibility
    world.set_weather(carla.WeatherParameters.ClearNoon)

    image_queue = queue.Queue()
    rgb_camera.listen(image_queue.put)

    try:
        print("Warming up camera and letting textures load...")
        # Tick 20 times to ensure the engine has fully loaded the high-res road textures
        for _ in range(20):
            world.tick()
            image_queue.get()

        print("Taking final zoomed-in, high-resolution screenshot...")
        world.tick()
        image = image_queue.get()

        filepath = 'output_print/High_Curve_Zoomed_Performance.png'
        image.save_to_disk(filepath)
        print(f"Success! Crisp image saved to: {filepath}")

    finally:
        rgb_camera.stop()
        rgb_camera.destroy()

        settings.synchronous_mode = False
        world.apply_settings(settings)

        # Reload the layers so your map isn't permanently bald for future scripts
        world.load_map_layer(carla.MapLayer.Foliage)
        world.load_map_layer(carla.MapLayer.Buildings)
        world.load_map_layer(carla.MapLayer.ParkedVehicles)

        print("Cleaned up and restored map layers.")


if __name__ == '__main__':
    main()
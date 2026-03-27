import time

boot_ticks = time.ticks_ms()

def check_uptime():
    # Calculate how many milliseconds have passed since the script started
    uptime_ms = time.ticks_diff(time.ticks_ms(), boot_ticks)
    return uptime_ms
    #print("Device has been running for", uptime_ms, "ms")
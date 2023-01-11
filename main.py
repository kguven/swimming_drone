#!/usr/bin/env python3

import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError, PositionNedYaw, VelocityBodyYawspeed, Attitude


async def run():

    drone = System()
    await drone.connect(system_address="udp://:14540")

    status_text_task = asyncio.ensure_future(print_status_text(drone))

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()
    await asyncio.sleep(10)
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: \
                  {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return

    await drone.action.land()
    await asyncio.sleep(15)

    print("-- Arming")
    await drone.action.arm()

    print("-- Setting initial setpoint")
    await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: \
                 {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return

    thrust = 0.3
    await drone.offboard.set_attitude(Attitude(0.0, -30.0, 0.0, thrust))
    await asyncio.sleep(5)
    await drone.offboard.set_attitude(Attitude(0.0, -30.0, 50.0, thrust))
    await asyncio.sleep(15)
    await drone.action.takeoff()
    status_text_task.cancel()


async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"Status: {status_text.type}: {status_text.text}")
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
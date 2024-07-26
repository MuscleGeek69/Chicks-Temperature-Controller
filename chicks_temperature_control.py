import appdaemon.plugins.hass.hassapi as hass
import asyncio
from datetime import datetime, timedelta

class ChicksTemperatureControl(hass.Hass):

    def initialize(self):
        self.temperature_sensor = self.args["temperature_sensors"]
        self.light_switches = self.args["light_switches"]
        self.target_temperature = self.args["target_temperature"]
        self.temperature_tolerance = self.args["temperature_tolerance"]
        self.overheat_threshold = self.args["overheat_threshold"]
        self.notification_service = self.args["notification_service"]
        self.check_interval = self.args["check_interval"]
        self.notification_cooldown = self.args.get("notification_cooldown", 3600)
        self.sun_sensor = "sun.sun"

        self.handle = None
        self.current_light_index = 0
        self.last_notification_time = None

        self.listen_state(self.check_temperature, self.temperature_sensor)
        self.listen_state(self.ensure_night_light, self.sun_sensor)
        self.log("ChicksTemperatureControl initialized")

    async def check_temperature(self, entity, attribute, old, new, kwargs):
        if new == old:
            return

        try:
            temp = await self.get_state(self.temperature_sensor, attribute="state")
            if not self.is_number(temp):
                self.log(f"No valid temperature readings available from {self.temperature_sensor}.", level="WARNING")
                return

            current_temperature = float(temp)
            temperature_difference = self.target_temperature - current_temperature

            if temperature_difference > self.temperature_tolerance:
                await self.turn_on_all_lights()
            elif 0 < temperature_difference <= self.temperature_tolerance:
                await self.turn_on_one_light()
            else:
                await self.turn_off_all_lights()

            if current_temperature > self.target_temperature + self.overheat_threshold:
                await self.notify_overheat(current_temperature)

        except (TypeError, ValueError) as e:
            self.log(f"Error reading temperature: {e}", level="ERROR")

    def is_number(self, s):
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False

    async def turn_on_all_lights(self):
        await asyncio.gather(*[self.turn_on(light) for light in self.light_switches])

    async def turn_off_all_lights(self):
        sun_state = await self.get_state(self.sun_sensor)
        if sun_state == "below_horizon":
            await self.turn_off_one_light()
        else:
            await asyncio.gather(*[self.turn_off(light) for light in self.light_switches])

    async def turn_off_one_light(self):
        if self.current_light_index >= len(self.light_switches):
            self.current_light_index = 0
        await self.turn_off(self.light_switches[self.current_light_index])
        self.current_light_index += 1

    async def turn_on_one_light(self):
        if self.current_light_index >= len(self.light_switches):
            self.current_light_index = 0
        await self.turn_on(self.light_switches[self.current_light_index])
        self.current_light_index += 1

    async def notify_overheat(self, current_temperature):
        message = f"Warning: Overheat detected! Current temperature is {current_temperature}°F."
        await self.call_service(self.notification_service, message=message)

    async def ensure_night_light(self, entity, attribute, old, new, kwargs):
        if new == "below_horizon":
            await self.ensure_one_light_on()

    async def ensure_one_light_on(self):
        light_states = await asyncio.gather(*(self.get_state(light) for light in self.light_switches))
        if not any(state == "on" for state in light_states):
            await self.turn_on_one_light()

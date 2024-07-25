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
        self.temperature_check_delay = self.args.get("temperature_check_delay", 1800)

        self.handle = None
        self.current_light_index = 0
        self.last_notification_time = None

        self.listen_state(self.check_temperature, self.temperature_sensor)
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
                await self.start_temperature_check(current_temperature)
            elif 0 < temperature_difference <= self.temperature_tolerance:
                await self.turn_on_one_light()
                await self.start_temperature_check(current_temperature)
            else:
                await self.turn_off_all_lights()
                await self.stop_temperature_check()

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

    async def start_temperature_check(self, current_temperature):
        if self.handle is not None:
            self.cancel_timer(self.handle)
        self.handle = self.run_in(self.check_if_temperature_rising, self.check_interval, current_temperature=current_temperature)

    async def stop_temperature_check(self):
        if self.handle is not None:
            self.cancel_timer(self.handle)
            self.handle = None

    async def check_if_temperature_rising(self, kwargs):
        await asyncio.sleep(self.temperature_check_delay)

        current_temperature = kwargs["current_temperature"]
        new_temp = await self.get_state(self.temperature_sensor, attribute="state")
        
        if not self.is_number(new_temp):
            return

        new_temperature = float(new_temp)
        light_states = await asyncio.gather(*(self.get_state(light) for light in self.light_switches))
        all_lights_on = all(state == "on" for state in light_states)
        
        if new_temperature < current_temperature and all_lights_on:
            await self.notify_temperature_drop(new_temperature)
        else:
            await self.stop_temperature_check()

    async def turn_on_all_lights(self):
        await asyncio.gather(*[self.turn_on(light) for light in self.light_switches])

    async def turn_off_all_lights(self):
        await asyncio.gather(*[self.turn_off(light) for light in self.light_switches])

    async def turn_on_one_light(self):
        if self.current_light_index >= len(self.light_switches):
            self.current_light_index = 0
        await self.turn_on(self.light_switches[self.current_light_index])
        self.current_light_index += 1

    async def notify_overheat(self, current_temperature):
        message = f"Warning: Overheat detected! Current temperature is {current_temperature}°F."
        await self.call_service(self.notification_service, message=message)

    async def notify_temperature_drop(self, current_temperature):
        current_time = datetime.now()
        if self.last_notification_time is None or (current_time - self.last_notification_time).total_seconds() > self.notification_cooldown:
            message = f"Alert: Temperature is dropping! Current temperature is {current_temperature}°F."
            await self.call_service(self.notification_service, message=message)
            self.last_notification_time = current_time

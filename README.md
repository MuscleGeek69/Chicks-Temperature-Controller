# Chicks Temperature Controller

The chicks temperature controller is an AppDaemon program that monitors and maintains chicks' temperatures using temperature sensors and light switches. This software keeps the chicks at a comfortable temperature by altering the lighting according to the current temperature data.

## How it Works

Temperature Monitoring: The app continually monitors the temperature using a set of configurable temperature sensors.

### Temperature Adjustment

- If the temperature drops below the target temperature by a certain tolerance, the app turns on all configured light switches to increase the temperature.  
- If the temperature is slightly below the target, it turns on one light switch in a round-robin fashion to evenly distribute heating.  
- If the temperature is above the target, it turns off all light switches.  
- There will always be one light turned on at night (round-robin) since chiks like to sleep with some warm lighting.  

### Notification System

- The app sends a notification if the temperature does not rise after turning on all lights, ensuring you are alerted to potential issues.  
- The app also sends a notification if the temperature rises above the target temperature by a certain threshold, preventing the chicks from overheating.  
- A notification will trigger if any of the light sensors or the temperature sensor becomes unavailable.  

## Configuration

To utilize this app, you must configure it in the apps.yaml file. This is an example configuration:

```ruby
chicks_temperature_controller:
  module: chicks_temperature_control
  class: ChicksTemperatureControl
  temperature_sensors: sensor.chick_coop_temperature_1
  light_switches:
    - switch.chick_coop_light_1
    - switch.chick_coop_light_2
    # Add more light switches here
  target_temperature: 90 
  temperature_tolerance: 2
  overheat_threshold: 5 
  notification_service: notify/mobile_app_user
  check_interval: 300  # Time in seconds to check if temperature is rising (e.g., 300 seconds = 5 minutes)
```

| Parameters | Description |
| -----------| ------------ |
| Temperature_sensors | Temperature entity that will be used to read the temperature inside chicks brooder. |
| Light_switches | A list of light switch entities that control the heating lights. |
| target_temperature | The desired temperature for the chicks (Fahrenheit). Once the temperature drops from the desired value, one of the lights (round-robin) will turn on in effort to bring back the temperature to this value. |
| Temperature_tolerance | This indicates the tolerance level before turning multiple lights at once. |
| overheat_threshold | Temperatures exceeding the desired temperature will cause an overheat alarm. |
| notification_service | The service to utilize to issue notifications. |
| check_interval | A time interval (in seconds) to determine whether the temperature is rising after turning on all lights. |

## Installation

Copy the AppDaemon application: Place the chicks_temperature_control.py file in the AppDaemon applications directory.
Update Configuration: Include the configuration in your apps.yaml file.
Reload the AppDaemon: To implement the changes, reload AppDaemon.

## Usage

Once installed and operating, the app will automatically monitor and manage the lights to keep your chicks at the proper temperature. You will receive messages if the temperature does not rise after turning on all lights, or if the temperature increases over a specified threshold, allowing you to take appropriate action.

## Warnings and Precautions

### Attention

Device Connectivity: Make sure all temperature sensors and light switches have a reliable connection to Home Assistant. If devices disconnect while the lights are turned on, the app may not operate properly, allowing the lights to remain on and overheat the chicks.
Regular Monitoring: To protect your chicks' safety and well-being, review the app's functioning and device connectivity on a consistent basis.
Emergency Preparedness: Prepare a manual emergency plan to handle any unforeseen situations, such as equipment failures or power outages.
By adhering to these rules and cautions, you can help guarantee that the chicks_temperature_controller app operates effectively and safely, allowing your chicks to live comfortably.

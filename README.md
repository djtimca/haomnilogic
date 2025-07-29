# Hayward Omnilogic Pool Controller

<a target="_blank" href="https://www.buymeacoffee.com/djtimca"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy me a coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;"></a> [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

This integration will provide sensors and control for Hayward Omnilogic based pool
controllers.

Sensors include:
- Water and Air Temperature Sensors
- Pump Speed Sensors
- Salt Level Sensors
- Chlorinator Sensors
- PH and ORP Sensors
- Pool Alarm Sensors

Controls include:
- Colorlogic light controls
- Pump on/off and speed controls
- Relay on/off controls
- Water Heater controls

## Install

Once installed, go to `Configuration -> Integrations` and click the + to add a new integration. On new instances of Home Assistant, `Settings -> Devices & Services -> Integrations` and click the **"+ ADD INTEGRATION"** in the bottom right to add the **Omnilogic** integration.

Search for **Omnilogic** and you will see the integration available.

Click add, confirm you want to install, and enter your email address and password
for your Hayward Omnilogic App login and everything should be added and available. A restart will be necessary in the process.

### Repository Missing from HACS Integration Search
If the Omnilogic integration isn't found, you may have to add the repository to HACS using the following steps
1. Open the HACS page/tab in Home Assistant
2. Navigate to the **"Integrations"** tab
3. Click on the three dots in the top right hand and select **"Custom repositories"** from the list of options
4. Copy and paste this repoistories link `https://github.com/djtimca/haomnilogic` and paste it into the **"Repository"** input field
5. Select **"Integration"** from the **"Category"** dropdown
6. Click **"Add"**
- Allow a few seconds for HACS to pull the latest information and data down. Once available, you'll be able to follow the install instructions above

Enjoy!

## Integration Usage

[Hayward OmniLogic](https://www.hayward-pool.com/shop/en/pools/omnilogic-i-auomni--1) smart pool and spa technology control.

There is currently support for the following device types within Home Assistant:

- ***Sensor*** - Air Temperature, Water Temperature, Variable Pump Speed, Chlorinator Setting, Instant and Average Salt Levels, pH, and ORP. Note that the Omnilogic controller allows temperature sensors to be renamed; sensors must be left at the default naming convention for the integration to properly recognize them (airTemp, waterTemp, etc.)
- ***Switch*** - All relays, pumps (single, dual, variable speed), relay-based lights, chlorinator control, and superchlorination control.
- ***Light*** - Colorlogic Lights (V1 and V2).
- ***Water Heater*** - Pool heaters of different types.

## Tips for Usage

Review the [Wiki](https://github.com/djtimca/haomnilogic/wiki) for tips on how I have used custom cards and a few helpers/tricks to get the most out of this integration for my pool!

## Sensor Platform Options

If you have pH sensors in your Omnilogic setup, you can add an offset to correct reporting from the sensor in the integration configuration.

Go to the Integrations page in setup and choose 'Configure' to adjust your offsets.

## Switch Platform

The switch platform contains custom services for pump speed control and chlorinator management.

### Pump Speed Control

To set pump speed on variable speed pumps, call the `omnilogic.set_pump_speed` service:

```yaml
# Modern format (recommended)
service: omnilogic.set_pump_speed
target:
  entity_id: switch.pool_pump
data:
  speed: 75

# Legacy format (still supported)
service: omnilogic.set_pump_speed
data:
  entity_id: switch.pool_pump
  speed: 75
```

### Chlorinator Control

The integration provides full chlorinator control with two switch entities:
- **Chlorinator Switch**: Controls the main chlorinator on/off state
- **Superchlorinate Switch**: Controls superchlorination mode (only available when chlorinator is on)

To set the chlorinator timed output percentage, use the `omnilogic.set_chlor_timed_percent` service:

```yaml
# Modern format (recommended)
service: omnilogic.set_chlor_timed_percent
target:
  entity_id: switch.chlorinator
data:
  timed_percent: 40

# Legacy format (still supported)
service: omnilogic.set_chlor_timed_percent
data:
  entity_id: switch.chlorinator
  timed_percent: 40
```

The timed_percent value must be between 0 and 100.

## Light Platform

The light platform allows you to set the color or effect of your lights from the effect list supported by your light version.

If you have V2 Colorlogic lights you can also set the brightness and speed of the lights using the custom service `omnilogic.set_v2_lights`:

```yaml
# Modern format (recommended)
service: omnilogic.set_v2_lights
target:
  entity_id: light.pool_lights
data:
  speed: 5
  brightness: 3

# Legacy format (still supported)
service: omnilogic.set_v2_lights
data:
  entity_id: light.pool_lights
  speed: 5
  brightness: 3
```

Both speed (0-8) and brightness (0-4) parameters are optional.

## Debugging integration

If you have problems with the integration, the first thing we will need to troubleshoot is the telemetry for your pool setup. Please:

1. Go to: https://replit.com/@djtimca/OmniTesting
2. Hit the 'Run' button at the top.
3. Enter your username and password
4. Hit Enter to clear your credentials
5. After the script finishes, your file names will be listed in the output (eg. `output_116_5216g89yd5_telemetry.json`, `output_116_2859af29q03_msconfig.xml`, `output_116_c8528gw23y_telemetry.xml`)
    - Click on the **"Show Files"** on the top left
    - Look for the respective file and click on it to open and view the content
        - It may be useful to `CTRL+F` for your file name as the sidebar view cannot be expanded
    - Copy the telemetry data from the files.
7. Post your telemetry when you open an issue in this repository as a json/XML code block so we can review and troubleshoot

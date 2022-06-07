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

Click add, confirm you want to install, and enter your username (not email) and password
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

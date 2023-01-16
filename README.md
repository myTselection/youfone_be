[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

# Youfone.be (Beta)
[Youfone.be](https://www.youfone.be/) Home Assistant custom component

<!-- <p align="center"><img src="https://github.com/myTselection/youfone_be/blob/main/logo.png"/></p> -->


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/youfone_be as custom repository (HACS > Integration > option: Custom Repositories)
- Restart Home Assistant
- Add 'Youfone.be' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide Youfone.be username and password
- Sensor `youfone_be_data` and `youfone_be_mobile` should become available with the percentage of data and call/sms left and extra attributes on usage and period start/end etc.

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/youfone_be/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code youfone.be/custom_components/youfone.be:
- [sensor.py](https://github.com/myTselection/youfone_be/blob/main/custom_components/youfone_be/sensor.py)
- [utils.py](https://github.com/myTselection/youfone_be/blob/main/custom_components/youfone_be/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

## Example usage:
### Gauge & Markdown
```
type: vertical-stack
cards:
  - type: markdown
    content: >
      <img src="https://raw.githubusercontent.com/myTselection/youfone_be/main/logo.png" width="30"/>  **Youfone.be**
      ### Total used:
      {{state_attr('sensor.youfone_be_phone','used_percentage')}}%
	  
	  TODO
  - type: gauge
    entity: sensor.youfone_be_phone
    max: 100
    min: 0
    needle: true
    unit: '%'
    name: ''
    severity:
      green: 0
      yellow: 60
      red: 80
```


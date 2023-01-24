[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

# Youfone.be (Beta)
[Youfone.be](https://www.youfone.be/) Home Assistant custom component. This custom component has been built from the ground up to bring your Youfone mobile phone usage details into Home Assistant to help you towards a better follow up on your usage information. This integration is built against the public website provided by Youfone Belgium and has not been tested for any other countries.

This integration is in no way affiliated with Youfone Belgium.

Some discussion on this topic can be found within [the Home Assistant community forum](https://community.home-assistant.io/t/youfone-be-custom-integration/520952).

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/youfone_be/master/icon.png"/></p>


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/youfone_be as custom repository (HACS > Integration > option: Custom Repositories)
- Restart Home Assistant
- Add 'Youfone.be' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide Youfone.be username and password
- Sensor `Youfone.be call sms` and `Youfone.be internet` should become available with the percentage of data and call/sms left and extra attributes on usage and period start/end etc.

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/youfone_be/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code youfone.be/custom_components/youfone.be:
- [sensor.py](https://github.com/myTselection/youfone_be/blob/master/custom_components/youfone_be/sensor.py)
- [utils.py](https://github.com/myTselection/youfone_be/blob/master/custom_components/youfone_be/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

## Example usage: (using [dual gauge card](https://github.com/custom-cards/dual-gauge-card))
### Gauge & Markdown
```
type: vertical-stack
  - type: markdown
    content: >-
      ## <img
      src="https://raw.githubusercontent.com/myTselection/youfone_be/master/icon.png"
      width="30"/>&nbsp;&nbsp;Youfone
      {{state_attr('sensor.youfone_be_call_sms','phone_number')}}


      ### Totaal bel/sms verbruikt: {{states('sensor.youfone_be_call_sms')}}%
      ({{state_attr('sensor.youfone_be_call_sms','includedvolume_usage')}} van
      {{state_attr('sensor.youfone_be_call_sms','total_volume')}})

      ### Totaal data verbruikt: {{states('sensor.youfone_be_internet')}}%
      ({{state_attr('sensor.youfone_be_internet','includedvolume_usage')}} van
      {{state_attr('sensor.youfone_be_internet','total_volume')}})

      #### {{state_attr('sensor.youfone_be_call_sms','period_days_left')|int}}
      dagen resterend
      ({{((state_attr('sensor.youfone_be_call_sms','total_volume')|replace('
      Min','')) or 0)|int -
      (state_attr('sensor.youfone_be_call_sms','includedvolume_usage') or
      0)|int}} Min)



      laatste update: *{{state_attr('sensor.youfone_be_call_sms','last update')
      | as_timestamp | timestamp_custom("%d-%m-%Y")}}*
       
  - type: custom:dual-gauge-card
    title: false
    min: 0
    max: 100
    shadeInner: true
    cardwidth: 350
    outer:
      entity: sensor.youfone_be_call_sms
      attribute: used_percentage
      label: used
      min: 0
      max: 100
      unit: '%'
      colors:
        - color: var(--label-badge-green)
          value: 0
        - color: var(--label-badge-yellow)
          value: 60
        - color: var(--label-badge-red)
          value: 80
    inner:
      entity: sensor.youfone_be_call_sms
      label: period
      attribute: period_used_percentage
      min: 0
      max: 100
      unit: '%'
      colors:
        - color: var(--label-badge-green)
          value: 0
        - color: var(--label-badge-yellow)
          value: 60
        - color: var(--label-badge-red)
          value: 80
  - type: history-graph
    entities:
      - entity: sensor.youfone_be_call_sms
    hours_to_show: 500
    refresh_interval: 60
```

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/youfone_be/master/Markdown%20Gauge%20Card%20example.png"/></p>

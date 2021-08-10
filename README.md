# apcaccess
Home Assistant plugin to track APC UPS using apcaccess and [apcupsd](http://www.apcupsd.org/)

### Basic config:
```
sensor:
  - platform: apcaccess
    host: 127.0.0.1
```

### Full Config:
```
sensor:
  - platform: apcaccess
    host: 127.0.0.1
    port: 3551
    timeout: 30
    sensor_timeout: 5
    power_calc: true
```


| Option         | Default     | Required | Description                                                                                                         |
|----------------|-------------|----------|---------------------------------------------------------------------------------------------------------------------|
| host           | `127.0.0.1` | Yes      | Host IP or URL of device running apcupsd                                                                            |
| port           | `3551`      | Yes      | Port of host device                                                                                                 |
| timeout        | `30`        | No       | How long to wait for device connection in seconds.                                                                  |
| sensor_timeout | `5`         | No       | How long to wait for sensor to respond after initialization in seconds. Could be important for automation purposes. |
| power_calc     | true        | No       | Determines if integration will create a sensor to track UPS power use. Measured in 'W'.                             |

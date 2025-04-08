# Software for the Central Analog Summing Board (CASB)
Written in Python3. Listens for a configuration file from the Data Aquisition System (DAQ), parses it, and sets thresholds and masks on the board accordingly. Digital to Analog Converter (DAC) output threshold voltages and Analog to Digical Converter (ADC) input voltages are communicated using I2C. Masks are switched on and off using GPIO. Writes firmware level configurables like reshape length to memory registers (add this).

### Directories
- `daq/` Use the contents of this folder to configure the CASB remotely 
- `zturn/` Code on the CASB's Z-Turn 

### Notes from CASB 1 and 2 deployment
- Only use the unity gain path's `high`, `medium`, `low`, and `time over threshold` compators.
- Do not use the attenuated gian path's `attenuated time over threshold` comparator
- **Leave analog input 2 off at all times** 

# How to connect to and configure the CASB 
Clone this repository
```bash
git clone git@github.com:hbjamin/casb-control.git
```

Navigate to the `daq` directory
```bash
cd daq/
```

Edit `config.json` to your desired CASB configuration
| Key | Value | Description |
|--------------------|---------------------------|-------------------------------------------------------------------------------------------------------|
| `channel_masks`         | list of ints   | Sets the mask of each channel. Leftmost entry is channel 1. Must be `0` (OFF) or `1` (ON) |
| `comparator_thresholds` | list of floats | Sets the **relative (above baseline)** threshold of each comparator. Must be between `0.02` and `3.19` Volts. Resolution is `0.00078` V | 
| `comparator_widths`     | list of floats | Sets the width of each comparator's trigger. Set to `1.7` for widest possible trigger. Must be between `0` and `3.19` Volts. Resolution is `0.00078` V | 

Perform initial configuration of the CASB. This includes:
- Scanning all settable baselines (this will take a minute)
- Setting the optimal basleine
- Setting comparator thesholds **realtive to baseline**
- Setting comparator output trigger widths
- Setting channel masks
- Constant baseline monitoring every minute until the script is killed 
```bash
python3 send_config.py config.json
```

# How to make changes to the CASB
**Always run** `setup.py` **first** so that the optimal baseline is set. After this, you can run `update.py` to update an individual CASB setting without performing another baseline scan or killing the baseline monitoring
```bash
python3 send_update.py [arg1] [arg2] [arg3] [arg4]
```

### Available arguments

| Argument          | Short Form | Type   | Default Value | Description                                                                                           |
|--------------------|------------|--------|---------------|-------------------------------------------------------------------------------------------------------|
| `--channel`        | `-c`       | int    | `None`        | Specifies the channel to update. Must be an integer between `1` and `20`.                            |
| `--mask`           | `-m`       | int    | `None`        | Specifies the mask value to update. Must be `0` (OFF) or `1` (ON).                                   |
| `--comparator`     | `-p`       | str    | `None`        | Specifies the comparator to update. Valid options are `h` (unity gian path high), `m` (unity gain path medium), `l` (unity gain path low), `t` (unity gain path time over threshold), or `a` (attenuated gain path time over threshold).                   |
| `--threshold`      | `-t`       | float  | `None`        | Specifies the threshold voltage for the comparator. Must be between `0` and `casb.dacVref`.          |
| `--width`          | `-w`       | float  | `None`        | Specifies the width for the comparator. Must be between `0` and `casb.dacVref`.                      |

### Examples
Turn channel 2 off
```bash
python3 send_update.py -c 2 -m 0
```

Set high comparator threshold to 800 mV
```bash
python3 send_update.py -p h -t 0.8
```

Set low comparator output as long as possible
```bash
python3 send_update.py -p l -w 1.7
```

### Map of outputs 
| SMB Connector (from top) | Description |
|---------------------------|-------------------------------------------------------------------------------------------------------|
| `1` | Unity path analog monitor before baseline restoration |
| `2` | **Unity path analog monitor after baseline restoration**  |
| `3` | Attenuated path analog monitor before baseline restoration |
| `4` | Attenuated path analog monitor after baseline restoration |
| `5` | **Unity path high comparator ECL output** |
| `6` | **Unity path medium comparator ECL output** |
| `7` | **Unity path low comparator ECL output** |
| `8` | **Unity path time over threshold comparator ECL output** |
| `9` | Attenuated path time over threshold comparator ECL output |
| `10`|  Spare ECL output 1 |
| `11`|  Spare ECL output 2 |
| `12`|  Lockout ECL input |
| `13`|  Delayed global trigger ECL input |
| `14`|  Spare ECL input 1 |
| `15`|  Spare ECL input 2 |

# Documentation for `zturn/` code  

- `/etc/init.d/socket_server` SysVinit script that manages the `socket_server.py` process, allowing one to start, stop, restart and check the status 
- `/home/petalinux/socket_server.py` Socket server that recieves configurations from the daq, runs `setup.py`, and streams its real-time log output back to the daq
- `/home/petalinux/setup.py` Performs a baseline scan, the initial CASB configuration, and constant baseline monitoring until killed

- `/etc/init.d/socket_update` SysVinit script that manages the `socket_update.py` process, allowing one to start, stop, restart and check the status 
- `/home/petalinux/socket_update.py` Socket server that recieves commands form the daq, runs `update.py`, and streams its real-time log output back to the daq
- `/home/petalinux/update.py` Updates one aspect of the CASB configuration 


# How to setup a SysVinit scipt

- Create python socket server script `socket_server.py` and place in `/home/petalinux/`
- Create init script `socket_server` for SysVinit and place at `/etc/init.d/socket_server`
- Make the init script exacutatble
```bash
sudo chmod +x /etc/init.d/socket_server
```
- Enable the init script to run on boot
```bash
sudo update-rc.d socket_server defaults
```
- Can also start and manage the service manually
```bash
sudo /etc/init.d/socket_server start
sudo /etc/init.d/socket_server stop
sudo /etc/init.d/socket_server restart
sudo /etc/init.d/socket_server status
```

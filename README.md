### CASB Control Code

- `daq/` Use the contents of this folder to configure the CASB remotely 
- `zturn/` (**DO NOT EDIT**) Code that lives on the CASB's Z-Turn 

### How to connect and configure the CASB 

Clone this repository
```bash
git clone git@github.com:hbjamin/casb-control.git
```

Navigate to the `daq` directory
```bash
cd daq/
```

Edit `config.json` 
| Key           | Value | Description |
|-------------------------|---------------|-------------------------------------------------------------------------------------------------------|
| `channel_masks`         | list of ints   | Sets the mask of each channel. Leftmost entry is channel 1. Must be `0` (OFF) or `1` (ON) |
| `comparator_thresholds` | list of floats | Sets the **relative (above baseline)** threshold of each comparator. Must be between 0-3 Volts. Resolution is 0.0008 V | 
| `comparator_widths`     | list of floats | Sets the width of each comparator's trigger. Set to 1.7 for widest possible trigger. Must be between 0-3 Volts. Resolution is 0.0008 V | 


### Available arguments

| Argument          | Short Form | Type   | Default Value | Description                                                                                           |
|--------------------|------------|--------|---------------|-------------------------------------------------------------------------------------------------------|
| `--channel`        | `-c`       | int    | `None`        | Specifies the channel to update. Must be an integer between `1` and `20`.                            |
| `--mask`           | `-m`       | int    | `None`        | Specifies the mask value to update. Must be `0` (OFF) or `1` (ON).                                   |
| `--comparator`     | `-p`       | str    | `None`        | Specifies the comparator to update. Valid options are `h`, `m`, `l`, `t`, or `a`.                   |
| `--threshold`      | `-t`       | float  | `None`        | Specifies the threshold voltage for the comparator. Must be between `0` and `casb.dacVref`.          |
| `--width`          | `-w`       | float  | `None`        | Specifies the width for the comparator. Must be between `0` and `casb.dacVref`.                      |

### Documentation  

1. **Python Script**: Socket server that listens for incoming JSON configuration files.
2. **Init Script**: Manages the Python socket server as a SysVinit service.
3. **Log File**: Captures essential output and errors from the Python script.
4. **Log Rotation Configuration**: Manages log file size and rotation to prevent excessive storage use.

## Step 1: Create Python Socket Server Script
- **File**: `/home/petalinux/socket_server.py`

---

## Step 2: Create Init Script for SysVinit
- **File**: `/etc/init.d/socket_server`
- **Make the Init Script Executable**:
```bash
sudo chmod +x /etc/init.d/socket_server
```
- **Enable the Script to Run on Boot**:
```bash
sudo update-rc.d socket_server defaults
```

---

## Step 3: Configure Log Rotation
- **File**: `/etc/logrotate.d/socket_server`

---

## Step 4: Start and Manage the Service
- **Start**:
```bash
sudo /etc/init.d/socket_server start
```
- **Stop**:
```bash
sudo /etc/init.d/socket_server stop
```
- **Check Status**:
```bash
sudo /etc/init.d/socket_server status
```
- **Restart**:
```bash
sudo /etc/init.d/socket_server restart
```

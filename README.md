# Central Analog Summing Board (CASB)
- `daq/` Use the contents of this folder to configure the CASB remotely 
- `zturn/` Code on the CASB's Z-Turn **(DO NOT EDIT EXCEPT FOR PRINT STATEMENTS)**

# Notes
- First CASB @ Berkeley
  - Only use the unity (actually `0.65`) gain path. This includes to the `high`, `medium`, `low`, and `time over threshold` comparators
  - Analog input 2 is noisy. **LEAVE OFF AT ALL TIMES**
  - IP `192.168.1.189`

# How to connect and configure the CASB 
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
| `--comparator`     | `-p`       | str    | `None`        | Specifies the comparator to update. Valid options are `h` (high), `m` (medium), `l` (low), `t` (time over threshold), or `a` (attenuated gain path time over threshold).                   |
| `--threshold`      | `-t`       | float  | `None`        | Specifies the threshold voltage for the comparator. Must be between `0` and `casb.dacVref`.          |
| `--width`          | `-w`       | float  | `None`        | Specifies the width for the comparator. Must be between `0` and `casb.dacVref`.                      |

### Documentation for `zturn/` code  

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

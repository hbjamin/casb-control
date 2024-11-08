## Overview
1. **Python Script**: Socket server that listens for incoming JSON configuration files.
2. **Init Script**: Manages the Python socket server as a SysVinit service.
3. **Log File**: Captures essential output and errors from the Python script.
4. **Log Rotation Configuration**: Manages log file size and rotation to prevent excessive storage use.

---

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

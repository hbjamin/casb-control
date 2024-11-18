import socket
import json
import subprocess
import datetime
import hashlib
import time
import shlex

server_port = 54322  # Port for receiving config
LOG_PORT = 65433     # Port for transmitting log 

def log_message(message):
    # Print to the terminal and log for debugging
    print(f"{datetime.datetime.now()}: {message}")

def generate_log_filename(config_file):
    with open(config_file, 'r') as f:
        config_content = f.read()
    config_hash = hashlib.md5(config_content.encode()).hexdigest()
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"/home/petalinux/logs/log_{timestamp}_{config_hash[:8]}.txt"

def connect_with_retry(client_daq_ip, port, retries=5, delay=2):
    """Attempt to connect to the DAQ with retries."""
    for attempt in range(retries):
        try:
            log_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            log_socket.connect((client_daq_ip, port))
            log_message("Connected to DAQ for log transmission.")
            return log_socket
        except socket.error as e:
            log_message(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    log_message("Failed to connect to DAQ after multiple attempts.")
    return None

def run_and_stream_setup(client_daq_ip, config_file):
    """Run setup.py and stream the output live to the DAQ."""
    print("Running setup.py")
    config_file=shlex.split(config_file)
    command = ["sudo", "-S", "python3", "-u", "/home/petalinux/update.py", *config_file]
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    process.stdin.write("petalinux\n")
    process.stdin.flush()

    log_message("Starting log stream...")
    log_filename = "/home/petalinux/logs/test.txt" 

    # Connect to the DAQ's log port and stream output
    with open(log_filename, "w") as log_file:
        log_socket = connect_with_retry(client_daq_ip, LOG_PORT)
        if not log_socket:
            log_message("Unable to send logs; DAQ connection was unsuccessful.")
            return

        with log_socket:
            for line in iter(process.stdout.readline, ''):
                log_message(line.strip())  # Log each line to the terminal
                log_file.write(line)       # Write to local log file
                log_file.flush()           # Ensure immediate write
                try:
                    log_socket.sendall(line.encode())
                except BrokenPipeError:
                    log_message("DAQ connection lost during log transmission.")
                    break

def start_server():
    log_message("Starting config server")
    server_address = '0.0.0.0'
    log_message(f"Listening on {server_address}:{server_port}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((server_address, server_port))
        s.listen()
        log_message(f"Listening on {server_address}:{server_port}")

        while True:
            client_socket, client_address = s.accept()
            daq_ip, _ = client_address  # Get DAQ's IP address
            log_message(f"Connected by {client_address}")
            with client_socket:
                data = client_socket.recv(1024).decode('utf-8')
                try:
                    #config = json.loads(data)
                    #config_file = "/home/petalinux/logs/latest_config.json"
                    #with open(config_file, "w") as f:
                    #    json.dump(config, f)
                    #log_message(f"Config saved to {config_file}")

                    # Start streaming setup.py output to the DAQ on log port
                    run_and_stream_setup(daq_ip, data)

                except json.JSONDecodeError:
                    log_message("Failed to decode JSON")
                except Exception as e:
                    log_message(f"Unexpected error: {e}")

if __name__ == "__main__":
    start_server()


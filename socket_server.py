import socket
import json
import subprocess
import datetime
import hashlib

LOG_PORT = 54322  # New port for log transmission

def log_message(message):
    # Print to the terminal and log for debugging
    print(f"{datetime.datetime.now()}: {message}")

def generate_log_filename(config_file):
    with open(config_file, 'r') as f:
        config_content = f.read()
    config_hash = hashlib.md5(config_content.encode()).hexdigest()
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"/home/petalinux/logs/log_{timestamp}_{config_hash[:8]}.txt"

def safe_send(client_socket, data):
    retries = 3
    for _ in range(retries):
        try:
            client_socket.sendall(data)
            return True
        except BrokenPipeError:
            log_message("Broken pipe; retrying...")
            continue
    return False

def run_and_stream_setup(client_daq_ip, config_file):
    """Run setup.py and stream the output live to the DAQ."""
    print("Running setup.py")
    command = ["sudo","-S","python3","-u","/home/petalinux/setup.py", config_file]
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    process.stdin.write("petalinux")
    process.stdin.flush()

    log_message("Starting log stream...")
    log_filename = generate_log_filename(config_file)

    # Connect to the DAQ's log port and stream output
    with open(log_filename, "w") as log_file:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as log_socket:
                log_socket.connect((client_daq_ip, 54322))
                log_message("Connected to DAQ for log transmission.")

                # Real-time line-by-line streaming
                for line in iter(process.stdout.readline, ''):
                    log_message(line.strip())  # Print to ZTurn terminal
                    log_file.write(line)
                    log_file.flush()
                    safe_send(log_socket, line.encode())
        except Exception as e:
            log_message(f"Failed to connect to DAQ on port 54322: {e}")

def start_server():
    log_message("START")
    server_address = '0.0.0.0'
    server_port = 54321
    log_message(f"Starting config server on {server_address}:{server_port}")

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
                    config = json.loads(data)
                    config_file = "/home/petalinux/logs/latest_config.json"
                    with open(config_file, "w") as f:
                        json.dump(config, f)
                    log_message(f"Config saved to {config_file}")

                    # Start streaming setup.py output to the DAQ on log port
                    run_and_stream_setup(daq_ip, config_file)

                except json.JSONDecodeError:
                    log_message("Failed to decode JSON")
                except Exception as e:
                    log_message(f"Unexpected error: {e}")

if __name__ == "__main__":
    start_server()

import sys
import socket
import json
import os
import datetime
from threading import Thread

def send_config(ip, port, config_path):
    # Send JSON config file to the server
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        data = json.dumps(config).encode('utf-8')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port))
            print(f"Connected to {ip}:{port} for config transmission")
            sock.sendall(data)
            print("Config file sent to CASB.")
    except (socket.error, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error during config transmission: {e}")
        sys.exit(1)

def receive_log_from_server():
    """Receive log output from the server and save to a log file."""
    log_directory = "daq_logs"
    os.makedirs(log_directory, exist_ok=True)
    log_file = os.path.join(log_directory, f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    # Open a server socket to listen on port 65432 for the incoming log stream
    with open(log_file, "w") as f:
        print(f"Receiving log output... saving to {log_file}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', 65432))
                s.listen(1)
                log_conn, _ = s.accept()  # Accept the connection from ZTurn
                print("Connected to ZTurn for log transmission")
                with log_conn:
                    while True:
                        chunk = log_conn.recv(1024)
                        if not chunk:
                            break
                        line = chunk.decode()
                        print(line, end='')  # Real-time print to DAQ terminal
                        f.write(line)
                        f.flush()

            print(f"Log transmission complete. Log saved to {log_file}")
        except socket.error as e:
            print(f"Error receiving log from server: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("ERROR! Please provide the CASB config file as the sole argument.")
        sys.exit(1)

    config_file = sys.argv[1]
    zturn_ip = "128.91.45.15"
    zturn_port = 54321

    # Start listening for the log in a separate thread
    log_listener_thread = Thread(target=receive_log_from_server)
    log_listener_thread.start()

    # Send configuration
    send_config(zturn_ip, zturn_port, config_file)

    # Wait for log reception to complete
    log_listener_thread.join()

if __name__ == "__main__":
    main()


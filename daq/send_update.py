import sys
import socket
import json
import os
import datetime
from threading import Thread


def send_args(host, port, args):
    """
    Sends command-line arguments to the socket server.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print(f"Connected to ZTurn at {host}:{port}")
            # Join the arguments into a single string
            args_str = ' '.join(args)
            #print(f"Sending arguments: {args_str}")
            s.sendall(args_str.encode('utf-8'))  # Send the arguments string
            # Wait for a response
            response = s.recv(1024).decode('utf-8')  # Adjust buffer size as needed
            #print(f"Server response: {response}")
    except ConnectionError as e:
        print(f"Failed to connect to server: {e}")
        sys.exit(1)

def receive_log_from_server():
    """Receive log output from the server and save to a log file."""
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)
    log_file = os.path.join(log_directory, f"log_{datetime.datetime.now().strftime('%Y_%b_%d_%Hh_%Mm_%Ss').lower()}.txt")

    # Open a server socket to listen on port 65432 for the incoming log stream
    with open(log_file, "w") as f:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', 65433))
                s.listen(1)
                log_conn, _ = s.accept()  # Accept the connection from ZTurn
                #print("Connected to ZTurn")
                print(f"Saving ZTurn output to {log_file}")
                with log_conn:
                    while True:
                        chunk = log_conn.recv(1024)
                        if not chunk:
                            break
                        line = chunk.decode()
                        print(line, end='')  # Real-time print to DAQ terminal
                        f.write(line)
                        f.flush()

            #print(f"Log transmission complete")
        except socket.error as e:
            print(f"Error receiving log from server: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("ERROR! Please provide valid arguments.")
        sys.exit(1)

    args = sys.argv[1:]
    zturn_ip = "192.168.1.189" # first CASB at Berkeley
    #zturn_ip = "128.91.45.15"
    zturn_port = 54322

    # Start listening for the log in a separate thread
    log_listener_thread = Thread(target=receive_log_from_server)
    log_listener_thread.start()

    # Send configuration
    send_args(zturn_ip, zturn_port, args)

    # Wait for log reception to complete
    log_listener_thread.join()

if __name__ == "__main__":
    main()


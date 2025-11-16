import socket
import json
from datetime import datetime

LOCAL_IP = '127.0.0.1'
LOCAL_PORT = 9090

REMOTE_IP = '54.71.128.194'
REMOTE_PORT = 92


### SOCKET HANDLING ###


def sendMSG(msg):
    try:
        with socket.socket() as client_sock:
            client_sock.connect((REMOTE_IP, REMOTE_PORT))
            client_sock.sendall(msg.encode())
            response = receive_full_msg(client_sock)
            return response

    # Catch sending messages errors
    except Exception as e:
        print(f"Error sending message to remote server: {e}")
        return ""


def receive_full_msg(client_sock):
    try:
        chunks = []
        while True:
            chunk = client_sock.recv(1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks).decode()

    # Catch receiving messages errors
    except Exception as e:
        print(f"Error receiving message: {e}")
        return ""


def proxy():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listening_sock:
            listening_sock.bind((LOCAL_IP, LOCAL_PORT))
            listening_sock.listen(1)

            while True:
                try:
                    client_soc, client_address = listening_sock.accept()
                    with client_soc:
                        try:
                            msg = receive_full_msg(client_soc)
                            print(f"Received message: {msg}")

                            response = sendMSG(msg)
                            print(f"Received response: {response}")

                            client_soc.sendall(response.encode())

                        # Catch errors handling message
                        except Exception as e:
                            print(f"Error handling client message: {e}")

                # Catch errors accepting connection
                except Exception as e:
                    print(f"Error accepting connection: {e}")

    # Catch errors setting up sockets
    except Exception as e:
        print(f"Error setting up proxy socket: {e}")


### MSG PROCESSING ###


# Decrypt text by xor
def xor_decrypt(data: str, key: str) -> str:
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))


def process_json(msg : str):
    try:
        data = json.loads(msg)

        if "students" in data:
            students = data["students"]
            print("Got students:", students)

        return data

    # Catch errors from json
    except Exception as e:
        print("JSON error:", e)
        return {}


def main():
    proxy()


if __name__ == "__main__":
    main()

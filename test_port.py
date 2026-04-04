import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 9009))
    print("Success: 127.0.0.1:9009")
    s.close()
except Exception as e:
    print(f"Failed: 127.0.0.1:9009 - {e}")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 9009))
    print("Success: 0.0.0.0:9009")
    s.close()
except Exception as e:
    print(f"Failed: 0.0.0.0:9009 - {e}")

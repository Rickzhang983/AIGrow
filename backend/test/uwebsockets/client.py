
import logging
import socket
import binascii
import random
import ssl



from .protocol import Websocket, urlparse

LOGGER = logging.getLogger(__name__)

def readline(sock):
    try:
        s = sock.readline()
    except AttributeError as e:
        from io import BytesIO
        s = BytesIO()
        while True:
            data = sock.recv()
            s.write(data)
            if b'\n' in data:
                break
    return s.getvalue().splitlines()[0]

class WebsocketClient(Websocket):
    is_client = True

def connect(uri):
    """
    Connect a websocket.
    """

    uri = urlparse(uri)
    assert uri

    sock = socket.socket()
    addr = socket.getaddrinfo(uri.hostname, uri.port)
    sock.connect(addr[0][4])
    if uri.protocol == 'wss':
        sock = ssl.wrap_socket(sock)

    def send_header(header, *args):
        sock.write(header % (args) )

    # Sec-WebSocket-Key is 16 bytes of random base64 encoded
    key = binascii.b2a_base64(bytes(random.getrandbits(8)
                                    for _ in range(16)))[:-1]

    send_header(b'GET %s HTTP/1.1\r\n', bytes(uri.path or '/',encoding = "utf-8"))
    send_header(b'Host: %s:%s\r\n', bytes(uri.hostname,encoding = "utf-8"),bytes(uri.port))
    send_header(b'Connection: Upgrade\r\n')
    send_header(b'Upgrade: websocket\r\n')
    send_header(b'Sec-WebSocket-Key: %s\r\n', key)
    send_header(b'Sec-WebSocket-Version: 13\r\n')
    send_header(b'Origin: http://localhost\r\n')
    send_header(b'\r\n')

    header = readline(sock)[:-2]
    assert header.startswith(b'HTTP/1.1 101 '), header


    return WebsocketClient(sock)

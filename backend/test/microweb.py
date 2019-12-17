import socket
from . import websocket_helper

try:
    import ustruct as struct
except:
    import struct

DEBUG = False


def websocket_write(socket, data):
    l = len(data)
    if l < 126:
        # TODO: hardcoded "binary" type
        hdr = struct.pack(">BB", 0x82, l)
    else:
        hdr = struct.pack(">BBH", 0x82, 126, l)
    socket.send(hdr)
    socket.send(data)


def recvexactly(socket, size):
    res = b""
    while size:
        data = socket.recv(size)
        if not data:
            break
        res += data
        size -= len(data)
    return res


def websocket_read(socket):
    while True:
        hdr = recvexactly(socket, 2)
        assert len(hdr) == 2
        firstbyte, secondbyte = struct.unpack(">BB", hdr)

        mskenable = True if secondbyte & 0x80 else False
        length = secondbyte & 0x7f
        print('content length=%d' % length)
        print('mskenable=' + str(mskenable))

        if length == 126:
            hdr = recvexactly(socket,2)
            assert len(hdr) == 2
            (length,) = struct.unpack(">H", hdr)
        if length == 127:
            hdr = recvexactly(socket,8)
            assert len(hdr) == 8
            (length,) = struct.unpack(">Q", hdr)
        print('content length=%d' % length)
        opcode = firstbyte & 0x0f
        if opcode == 8:
            socket.close()
            return '' #TBD raise an exception
        fin = True if firstbyte & 0x80 else False
        print('fin=' + str(fin))
        print('opcode=%d' % opcode)
        if mskenable:
            hdr = recvexactly(socket,4)
            assert len(hdr) == 4
            (msk1, msk2, msk3, msk4) = struct.unpack(">BBBB", hdr)
            msk = [msk1, msk2, msk3, msk4]
        data = []
        while length:
            skip = socket.recv(length)
            length -= len(skip)
            data.extend(skip)
        newdata = []
        # 解码数据
        for i, item in enumerate(data):
            j = i % 4
            newdata.append(chr(data[i] ^ msk[j]))
        res = ''.join(newdata)
        return res


class websocket_server:
    def __init__(self, s):
        self.socket = s


def main():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 8008))
    sock.listen(5)
    print('websokcet listen at 8008...')
    while True:
        # 这里阻塞接收客户端
        conn, address = sock.accept()
        # 接收到socket
        print('client connect...:')
        print(address)
        websocket_helper.server_handshake(conn)
        ws = websocket(conn)
        print('websocket connect succ')
        # conn.send('hello friend')
        while True:
            text = ws.read()
            if text == '':
                break
            print(text)

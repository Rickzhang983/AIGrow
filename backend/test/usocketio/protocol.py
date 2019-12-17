"""
Socket.io/Engine.io protocol constructs
"""

PAYLOAD_STRING = 0
PAYLOAD_BINARY = 1

PACKET_OPEN = 0
PACKET_CLOSE = 1
PACKET_PING = 2
PACKET_PONG = 3
PACKET_MESSAGE = 4
PACKET_UPGRADE = 5
PACKET_NOOP = 6

MESSAGE_CONNECT = 0
MESSAGE_DISCONNECT = 1
MESSAGE_EVENT = 2
MESSAGE_ACK = 3
MESSAGE_ERROR = 4
MESSAGE_BINARY_EVENT = 5
MESSAGE_BINARY_ACK = 6


def decode_packet(buf):
    if isinstance(buf, str) and buf[0] == 'b':
        # FIXME: implement base64 protocol
        raise NotImplementedError()

    return int(buf[0]), buf[1:]


def decode_payload(buf):
    buf = memoryview(buf)

    while buf:
        type_ = buf[0]
        buf = buf[1:]

        length = 0

        while True:
            c = buf[0]
            buf = buf[1:]

            if c == 0xff:
                break

            length *= 10
            length += c

        packet = bytes(buf[:length])

        if type_ == PAYLOAD_STRING:
            packet = packet.decode('utf-8')
        elif type_ == PAYLOAD_BINARY:
            pass
        else:
            raise NotImplementedError()

        yield decode_packet(packet)

        buf = buf[length:]

import socket

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

    ws = websocket(conn)
    print('websocket connect succ')
    # conn.send('hello friend')
    while True:
        text = ws.read()
        if text =='':
            break
        print(text)

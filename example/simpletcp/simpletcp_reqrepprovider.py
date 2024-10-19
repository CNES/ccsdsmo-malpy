#! /bin/python3

import sys
sys.path.append('../../src')

import threading

from malpy.mo import mal
from malpy.transport.tcp import TCPSocket
from malpy.encoding.pickle import PickleEncoder


def clientthread(socket):
    enc = PickleEncoder()
    request = mal.RequestProviderHandler(socket, enc)
    try:
        message = request.receive_request()
        print("[**] Received '{}'".format(message.msg_parts.decode('utf8')))
    except Exception as e:
        request.error("ERROR !".encode('utf8'))
    else:
        request.response("I got it!".encode('utf8'))
    finally:
        print("[**] Closing connection with %s %d." % (socket.uri[0], socket.uri[1]))
        socket.disconnect()


def main():
    host = '127.0.0.1'
    port = 8009

    s = TCPSocket()
    s.bind((host, port))
    s.listen(10)
    print("[*] Server listening on %s %d" % (host, (port)))

    try:
        while True:
            newsocket = s.waitforconnection()
            print("[**] Incoming connection from %s %d" % (newsocket.uri[0], newsocket.uri[1]))
            threading.Thread(
                target=clientthread,
                args=(newsocket, )
                ).start()

    except KeyboardInterrupt:
        s.unbind()
        sys.exit(0)


if __name__ == "__main__":
    main()

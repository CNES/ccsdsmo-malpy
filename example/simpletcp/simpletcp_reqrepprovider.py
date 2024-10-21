#! /bin/python3

import sys
sys.path.append('../../src')

import threading

from malpy.mo import mal
from malpy.transport import tcp
from malpy import encoding


class MyRequestProviderHandler(mal.RequestProviderHandler):
    AREA = 100
    AREA_VERSION = 1
    SERVICE = 1
    OPERATION = 1


def clientthread(socket):
    enc = encoding.PickleEncoder()
    request = MyRequestProviderHandler(socket, enc)
    try:
        message = request.receive_request()
        print("[***] Received '{}'".format(message.msg_parts.decode('utf8')))
    except mal.MALError as e:
        print("[!!!] Received an error")
        print("[!!!] "+ str(e))
        request.error([mal.UInteger(e.error.value), mal.Element(None)])
    else:
        request.response("I got it!".encode('utf8'))
    finally:
        print("[**] Closing connection with %s %d." % (socket.uri[0], socket.uri[1]))
        socket.disconnect()


def main():
    host = '127.0.0.1'
    port = 8009

    s = tcp.TCPSocket()
    s.bind((host, port))
    try:
        s.listen(10)
        print("[*] Server listening on %s %d" % (host, (port)))

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

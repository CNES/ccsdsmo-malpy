#! /bin/python3

import sys
sys.path.append('../../src')

import threading

from malpy.mo import mal
from malpy.transport import http
from malpy import encoding


class MyRequestProviderHandler(mal.RequestProviderHandler):
    AREA = 100
    VERSION = 1
    SERVICE = 1
    OPERATION = 1


def clientthread(socket):
    enc = encoding.XMLEncoder()
    request = MyRequestProviderHandler(socket, enc)
    message = request.receive_request()
    print("[**] Received '{}'".format(message.msg_parts))
    request.response(mal.String("I got it!"))

    print("[**] Closing connection with %s %d." % (socket.uri[0], socket.uri[1]))
    socket.disconnect()


def main():
    try:
        host = '127.0.0.1'
        port = 8009

        s = http.HTTPSocket()
        s.bind((host, port))
        s.listen(10)
        print("[*] Server listening on %s %d" % (host, (port)))

        while True:
            newsocket = s.waitforconnection()
            print("[**] Incoming connection from %s %d"
                  % (newsocket.uri[0], newsocket.uri[1]))
            threading.Thread(target=clientthread,
                             args=(newsocket,)
                             ).start()
        s.unbind()

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

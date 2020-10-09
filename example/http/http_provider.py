#! /bin/python

import sys
sys.path.append('../../src')

import threading

from mo import mal
from transport import http
import encoding


def clientthread(socket):
    enc = encoding.XMLEncoder()
    request = mal.RequestProviderHandler(socket, enc)
    message = request.receive_request()
    print("[**] Received '{}'".format(message.msg_parts))
    request.response(mal.String("I got it!"))
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

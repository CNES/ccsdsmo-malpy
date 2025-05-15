#! /bin/python3

# SPDX-FileCopyrightText: 2025 Olivier Churlaud <olivier@churlaud.com>
# SPDX-FileCopyrightText: 2025 CNES
#
# SPDX-License-Identifier: MIT

import sys
sys.path.append('../../src')

import threading

from malpy.mo import mal
from malpy.transport import tcp
from malpy import encoding


def clientthread(socket):
    enc = encoding.PickleEncoder()
    request = mal.RequestProviderHandler(socket, enc)
    message = request.receive_request()
    print("[**] Received '{}'".format(message.msg_parts.decode('utf8')))
    request.response("I got it!".encode('utf8'))
    print("[**] Closing connection with %s %d." % (socket.uri[0], socket.uri[1]))
    socket.disconnect()


def main():
    try:
        host = '127.0.0.1'
        port = 8009

        s = tcp.TCPSocket()
        s.bind((host, port))
        s.listen(10)
        print("[*] Server listening on %s %d" % (host, (port)))

        while True:
            newsocket = s.waitforconnection()
            print("[**] Incoming connection from %s %d" % (newsocket.uri[0], newsocket.uri[1]))
            threading.Thread(
                target=clientthread,
                args=(newsocket, )
                ).start()
        s.unbind()

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

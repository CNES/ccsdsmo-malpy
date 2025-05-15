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

CONTENT_TO_SEND = "../../README.md"


def clientthread(socket):
    enc = encoding.PickleEncoder()
    progress = mal.ProgressProviderHandler(socket, enc)
    message = progress.receive_progress()
    print("[**] Received '{}'".format(message.msg_parts.decode('utf8')))
    progress.ack("Coming!")
    with open(CONTENT_TO_SEND, 'rb') as f:
        content_size = 0
        while True:
            datatosend = f.readline()
            if len(datatosend) > 0:
                content_size += len(datatosend)
                progress.update(datatosend)
                print("[***] Sending: {}".format(datatosend))
            else:
                progress.response(content_size)
                break
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

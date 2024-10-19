#! /bin/python3

import sys
sys.path.append('../../src')

import threading

from malpy.mo import mal
from malpy.transport.tcp import TCPSocket
from malpy.encoding.pickle import PickleEncoder

CONTENT_TO_SEND = "../../README.md"


def clientthread(socket):
    enc = PickleEncoder()
    progress = mal.ProgressProviderHandler(socket, enc)
    message = progress.receive_progress(mal.String)
    print("[**] Received '{}'".format(message.msg_parts._internal_value))
    progress.ack(mal.String("Coming!"))
    with open(CONTENT_TO_SEND, 'rb') as f:
        content_size = 0
        while True:
            datatosend = f.readline()
            if len(datatosend) > 0:
                content_size += len(datatosend)
                progress.update(mal.String(datatosend.decode('utf-8')))
                print("[***] Sending: {}".format(datatosend))
            else:
                progress.response(mal.Integer(content_size))
                break
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

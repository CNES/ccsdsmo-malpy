#! /bin/python3

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
    try: 
        message = progress.receive_progress()
        print("[**] Received '{}'".format(message.msg_parts.decode('utf8')))
        progress.ack("Coming!")
    except mal.MALError as e:
        print("[!!!] Received an error")
        print("[!!!] "+ str(e))
        progress.ack_error([mal.UInteger(e.error.value), mal.Element(None)])
    except mal.InvalidInteractionStageError as e:
        print("[!!!] Received an error")
        print("[!!!] "+str(e))
    else:
        with open(CONTENT_TO_SEND, 'rb') as f:
            content_size = 0
            while True:
                datatosend = f.readline()
                if len(datatosend) > 0:
                    content_size += len(datatosend)
                    progress.update([mal.Blob(datatosend)])
                    print("[***] Sending: {}".format(datatosend))
                else:
                    progress.response(content_size)
                    break
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

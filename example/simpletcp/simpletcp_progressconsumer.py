#! /bin/python3

import sys
sys.path.append('../../src')

from malpy.mo import mal
from malpy.transport.tcp import TCPSocket
from malpy.encoding.pickle import PickleEncoder


def main():

    host = '127.0.0.1'
    port = 8009

    s = TCPSocket()
    enc = PickleEncoder()
    progress = mal.ProgressConsumerHandler(s, enc, "myprovider", "live_session")
    progress.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    progress.progress(mal.String("README.md"))
    progress.receive_ack([])
    result = ""
    while True:
        partial_result = progress.receive_update(mal.String)
        if progress.interaction_terminated:
            print("[**] Response: {}".format(partial_result.msg_parts._internal_value))
            break
        else:
            print("[**] Received part: {}".format(partial_result.msg_parts._internal_value[:-1])) # Remove the \n at the end of the line
            result += partial_result.msg_parts._internal_value
    print("[*] Received:\n{}\n{}\n{}".format('-'*10, result, '-'*10))

if __name__ == "__main__":
    main()

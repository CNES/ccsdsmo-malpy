#! /bin/python3

# SPDX-FileCopyrightText: 2025 Olivier Churlaud <olivier@churlaud.com>
# SPDX-FileCopyrightText: 2025 CNES
#
# SPDX-License-Identifier: MIT

import sys
sys.path.append('../../src')

from malpy.mo import mal
from malpy.transport import tcp
from malpy import encoding


def main():

    host = '127.0.0.1'
    port = 8009

    s = tcp.TCPSocket()
    enc = encoding.PickleEncoder()
    request = mal.RequestConsumerHandler(s, enc, "myprovider", "live_session")
    request.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    request.request("Hello world!".encode('utf8'))
    message = request.receive_response()
    print("[*] Received '{}'".format(message.msg_parts.decode('utf8')))


if __name__ == "__main__":
    main()

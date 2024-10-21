import socket as pythonsocket
import struct

from malpy.malpydefinitions import MALPY_ENCODING
from malpy.mo import mal

from .abstract_transport import MALSocket


class TCPSocket(MALSocket):

    _messagesize = 1024

    def __init__(self, socket=None):
        if socket:
            self.socket = socket
        else:
            self.socket = pythonsocket.socket(pythonsocket.AF_INET, pythonsocket.SOCK_STREAM)

    def bind(self, uri):
        """ @param uri: (host, port) """
        self.socket.bind(uri)

    def listen(self, unacceptedconnectnb=0):
        self.socket.listen(unacceptedconnectnb)

    def waitforconnection(self):
        conn, _ = self.socket.accept()
        return TCPSocket(conn)

    def connect(self, uri):
        """ @param uri: (host, port) """
        self.socket.connect(uri)

    def unbind(self):
        self.socket.close()

    def disconnect(self):
        self.socket.close()

    def send(self, message):
        self.socket.send(struct.pack('I', len(message)))
        self.socket.send(message)

    def recv(self):
        msg_size = struct.unpack('I', self.socket.recv(4))[0]
        message = self.socket.recv(msg_size)
        return message

    @property
    def uri(self):
        return self.socket.getsockname()



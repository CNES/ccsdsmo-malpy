import socket as pythonsocket

from malpydefinitions import MALPY_ENCODING
from mo import mal

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
        self.socket.send(message)

    def recv(self):
        return self.socket.recv(self._messagesize)

    @property
    def uri(self):
        return self.socket.getsockname()



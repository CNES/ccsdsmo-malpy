class MALSocket(object):

    def bind(self, uri):
        raise NotImplementedError("This is to be implemented.")

    def connect(self, uri):
        raise NotImplementedError("This is to be implemented.")

    def unbind(self):
        raise NotImplementedError("This is to be implemented.")

    def disconnect(self):
        raise NotImplementedError("This is to be implemented.")

    def send(self, message):
        raise NotImplementedError("This is to be implemented.")

    def recv(self):
        raise NotImplementedError("This is to be implemented.")
        message = b""
        return message

import socket as pythonsocket
class TCPSocket(MALSocket):

    _messagesize = 1024

    def __init__(self, socket = None):
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


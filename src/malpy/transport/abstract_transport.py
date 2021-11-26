class MALSocket(object):
    parent = None

    @property
    def encoding(self):
        if self.parent:
            if self.parent.encoding:
                return self.parent.encoding.encoding

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

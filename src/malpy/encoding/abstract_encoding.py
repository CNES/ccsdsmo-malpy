class Encoder(object):
    encoding = None
    parent = None

    def encode(self, message):
        raise NotImplementedError("This is to be implemented.")
        return message

    def decode(self, message, signature):
        raise NotImplementedError("This is to be implemented.")
        return message
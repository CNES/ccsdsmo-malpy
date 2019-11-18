import pickle

from malpydefinitions import MALPY_ENCODING

class Encoder(object):
    encoding = None

    def encode(self, message):
        raise NotImplementedError("This is to be implemented.")
        return message

    def decode(self, message):
        raise NotImplementedError("This is to be implemented.")
        return message


class PickleEncoder(Encoder):
    encoding = MALPY_ENCODING.PICKLE

    def encode(self, message):
        return pickle.dumps(message)

    def decode(self, message):
        return pickle.loads(message)

class XMLEncoder(Encoder):
    encoding = MALPY_ENCODING.XML

    def encode(self, message):
        return pickle.dumps(message)

    def decode(self, message):
        return pickle.loads(message)

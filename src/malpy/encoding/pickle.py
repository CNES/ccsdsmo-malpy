import pickle

from malpy.malpydefinitions import MALPY_ENCODING

from .abstract_encoding import Encoder


class PickleEncoder(Encoder):
    encoding = MALPY_ENCODING.PICKLE

    def encode(self, message):
        return pickle.dumps(message)

    def decode(self, message, signature):
        _ = signature
        return pickle.loads(message)

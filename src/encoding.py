import pickle
import xml.dom

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
        dom = xml.dom.getDOMImplementation()
        d = dom.createDocument('http://www.ccsds.org/schema/malxml/MAL', 'malxml:Body', None)
        d.firstchild.appendChild(d.createElement('malxml.Element')
        messagebody = d.toxml(encoding="UTF-8")
        return message

    def decode(self, message):
        return pickle.loads(message)

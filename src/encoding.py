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

MAL_XML_NAMESPACE_URL = "http://www.ccsds.org/schema/malxml/MAL"
MAL_XML = "xmlns:malxml"
XML_XSI_NAMESPACE_URL = "http://www.w3.org/2001/XMLSchema-instance"
XML_NAMESPACE = "http://www.w3.org/2000/xmlns/"
XMLNS_XSI = "xmlns:xsi"
XMLNS = "xmlns"

class XMLEncoder(Encoder):
    encoding = MALPY_ENCODING.XML

    def encode(self, message):

        def _encode_internal(element, parent):
            domdoc = parent.ownerDocument
            nodename = element.attribName or type(element).__name__
            subnode = parent.appendChild(domdoc.createElement(nodename))
            if element.value is None:
                subnode.setAttribute('xsi:nil', 'true')
            # if it's a list, it means this is a composite or a list of thing
            elif type(element.value) is list:
                for subelement in element.value:
                    _encode_internal(subelement, subnode)
            # else it's an attribute
            else:
                attributenode = subnode.appendChild(domdoc.createElement(type(element).__name__))
                attributenode.appendChild(domdoc.createTextNode(str(element.value)))

        dom = xml.dom.getDOMImplementation()
        d = dom.createDocument('http://www.ccsds.org/schema/malxml/MAL', 'malxml:Body', None)
        rootElement = d.firstChild

        rootElement.setAttributeNS(XML_NAMESPACE, XMLNS_XSI, XML_XSI_NAMESPACE_URL);
        rootElement.setAttributeNS(XML_NAMESPACE, MAL_XML, MAL_XML_NAMESPACE_URL);

        for element in message:
            _encode_internal(element, rootElement)
        encodedmessage = d.toprettyxml(encoding="UTF-8")
        return encodedmessage


    def decode(self, message):
        def _decode_internal(node, value):
            pass

        d = xml.dom.minidom.parseString(message)
        rootElement = d.firstChild
        for element in rootElement.childNodes:
            if element.nodeType is element.ELEMENT_NODE:
                pass

        return domdoc

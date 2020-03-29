import pickle
import xml.dom
import re
import sys

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

            # The node name is attribName if it exists, otherwise its type
            # ex: <longElement> ?? </longElement> or <Identifier> ?? </Identifier>
            nodename = element.attribName or type(element).__name__
            subnode = parent.appendChild(domdoc.createElement(nodename))

            # Deal with the Null type:
            if element.value is None:
                # ex: <longElement xsi:nul="True" /> or <Identifier xsi:nul="True" />
                # It's a leaf, we don't recurse deeper.
                subnode.setAttribute('xsi:nil', 'true')
            # if it's a list, it means this is a composite or a list of thing
            elif type(element.value) is list:
                # so we recurse over each item and append them below the objects
                # ex: the ?? is defined with se same algorithm
                for subelement in element.value:
                    _encode_internal(subelement, subnode)
            # else it's an attribute we add a subnode
            else:
                # ex: <longElement><Long>9</Long><longElement> or <Identifier><Identifier>LIVE</Identifier></Identifier>
                # It's a leaf, we don't recurse deeper.
                attributenode = subnode.appendChild(domdoc.createElement(type(element).__name__))
                attributenode.appendChild(domdoc.createTextNode(str(element.value)))


        dom = xml.dom.getDOMImplementation()

        # Create the document header and its namespaces
        d = dom.createDocument('http://www.ccsds.org/schema/malxml/MAL', 'malxml:Body', None)
        rootElement = d.firstChild

        rootElement.setAttributeNS(XML_NAMESPACE, XMLNS_XSI, XML_XSI_NAMESPACE_URL);
        rootElement.setAttributeNS(XML_NAMESPACE, MAL_XML, MAL_XML_NAMESPACE_URL);

        # Recursively go through the object to encode it (a composite is a list of list)
        for element in message.value:
            _encode_internal(element, rootElement)
        encodedmessage = d.toprettyxml(encoding="UTF-8")
        return encodedmessage


    def decode(self, message):
        # If the XML document was indented, there will be text node made of tabs
        # and newline characters. Those are not relevant for decoding.
        emptyNodePattern = re.compile(r"^[\n\t]*$")


        def _decode_internal(node):
            internal = []
            for element in node.childNodes:
                if element.nodeType is element.TEXT_NODE:
                    if not re.match(emptyNodePattern, element.nodeValue):
                        print("leaf TEXTE: {}".format(element.nodeValue))
                        internal.append(element.nodeValue)
                elif element.nodeType is element.ELEMENT_NODE:
                    if element.hasAttribute('xsi:nil') and element.getAttribute('xsi:nil'):
                        print("leaf ELSE: NULL")
                        internal.append(None)
                    else:
                        internal.append(_decode_internal(element))
                else:
                    raise RuntimeError(element)
            return internal

        d = xml.dom.minidom.parseString(message)
        rootElement = d.firstChild
        value = _decode_internal(rootElement)
        print(value)
        return value

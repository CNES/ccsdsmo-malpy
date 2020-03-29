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

        for element in message.value:
            _encode_internal(element, rootElement)
        encodedmessage = d.toprettyxml(encoding="UTF-8")
        return encodedmessage


    def decode(self, message):
        emptyNodePattern = re.compile(r"^[\n\t].*$")
        """"
                    /**
            * Logic to remove extra spaces, tabs, and line-breaks.
            * 1. Find all extra text elements.
            * 2. if it has no parent or parent is ROOT, remove
            * 2.1. if the parent has more than 1 elements, remove
            *
            * @param document XML Document
            * @throws XPathExpressionException rquired for XPaths
            */
            private static void emptyNodeRemoval(Document document) throws XPathExpressionException {
                XPathFactory xpathFactory = XPathFactory.newInstance();
                // XPath to find empty text nodes.
                XPathExpression xpathExp = xpathFactory.newXPath().compile(
                        "//text()[normalize-space(.) = '']");
                NodeList emptyTextNodes = (NodeList)
                        xpathExp.evaluate(document, XPathConstants.NODESET);

                // Remove each empty text node from document.
                for (int i = 0; i < emptyTextNodes.getLength(); i++) {
                    Node emptyTextNode = emptyTextNodes.item(i);
                    Node parentNode = emptyTextNode.getParentNode();

                    if (!(!Objects.isNull(parentNode) && !parentNode.getNodeName().equals(Constants.ROOT_ELEMENT) &&
                            parentNode.getChildNodes().getLength() == 1))  {
                        emptyTextNode.getParentNode().removeChild(emptyTextNode);
                    }
                }
            }
        """


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

        #clean_message = message.replace('\t', '').replace('\n', '')
        d = xml.dom.minidom.parseString(message)
        rootElement = d.firstChild
        value = _decode_internal(rootElement)
        print(value)
        return value

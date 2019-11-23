#! /bin/python

import xml.etree.ElementTree as ET
import yaml

MAL_FILE = "../xml/CCSDS-MO-MAL.xml"
MAL_NS = "http://www.ccsds.org/schema/ServiceSchema"
OUTFILE = "../src/mal/maltypes.py"
PARAMFILE = 'parameters.yaml'

class Area(object):
    name = ""
    number = 0
    version = 0
    comment = None

class Service(object):
    pass

class MALElementXML(object):
    __slots__ = ['name', 'fundamental', 'shortFormPart', 'comment', 'extends']
    datatype = "Element"

    def __init__(self, node=None):
        self.fundamental = False
        self.name = None
        self.comment = None
        self.extends = None
        self.shortFormPart = None
        if node is not None:
            self.parse(node)

    def parse(self, node):
        self.name = node.attrib['name']
        self.fundamental = ( node.tag == tag('fundamental') )
        self.shortFormPart = node.attrib.get('shortFormPart', None)
        self.comment = node.attrib.get('comment', None)
        if node.tag == tag('attribute'):
            self.extends = MALTypeXML()
            self.extends.area = 'MAL'
            self.extends.name = 'Attribute'
            self.extends.isList = False
        elif len(node) > 0:
            extends_node = list(node)[0]
            if extends_node.tag == tag('extends'):
                if len(extends_node) != 1:
                    raise RuntimeError("In {}, mal:extends has more than one subnode".format(self.name))
                self.extends = MALTypeXML(list(extends_node)[0])
        else:
            self.extends = None


class MALTypeXML(object):
    __slots__ = ['name', 'area', 'isList']
    datatype = "Type"

    def __init__(self, node=None):
        self.name = None
        self.area = None
        self.isList = None
        if node is not None:
            self.parse(node)

    def parse(self, node):
        self.name = node.attrib['name']
        self.area = node.attrib['area']
        self.isList = ( node.attrib.get('list', 'false') == 'true' )

class MALCompositeFieldXML(object):
    __slots__ = ['name', 'comment', 'canBeNull', 'maltype']
    datatype = "CompositeField"

    def __init__(self, node=None):
        self.name = None
        self.comment = None
        self.canBeNull = None
        self.maltype = None
        if node is not None:
            self.parse(node)

    def parse(self, node):
        self.name = node.attrib['name']
        self.canBeNull = ( node.attrib.get('canBeNull', 'true') == 'true' )
        self.comment = node.get('comment', None)
        if len(list(node)) != 1:
            raise RuntimeError("In {}, mal:field has more than one subnode".format(self.name))
        self.maltype = MALTypeXML(list(node)[0])

class MALCompositeXML(object):
    __slots__ = ['name', 'comment', 'shortFormPart', 'extends', 'fields']
    datatype = "Composite"

    def __init__(self, node=None):
        self.name = None
        self.comment = None
        self.extends = None
        self.shortFormPart = None
        self.fields = []
        if node is not None:
            self.parse(node)

    def parse(self, node):
        self.name = node.attrib['name']
        self.shortFormPart = node.attrib.get('shortFormPart', None)
        self.comment = node.attrib.get('comment', None)
        for subnode in node:
            if subnode.tag == tag('extends'):
                if len(list(subnode)) != 1:
                    raise RuntimeError("In {}, mal:extends has more than one subnode".format(self.name))
                self.extends = MALTypeXML(list(subnode)[0])
            elif subnode.tag == tag("field"):
                self.fields.append(MALCompositeFieldXML(subnode))
            else:
                raise RuntimeError("Did not expect {} tag in Composite.".format(subnode.tag))

class MALEnumerationItemXML(object):
    __slots__ = ['value', 'nvalue', 'comment']
    datatype = "EnumerationItem"

    def __init__(self, node=None):
        self.value = None
        self.comment = None
        self.nvalue = None
        if node is not None:
            self.parse(node)

    def parse(self, node):
        if node.tag != tag('item'):
            raise RuntimeError("Expected 'item', got {}".format(node.tag))
        self.value = node.attrib['value']
        self.nvalue = node.attrib['nvalue']
        self.comment = node.attrib.get('comment', None)

class MALEnumerationXML(object):
    __slots__ = ['name', 'comment', 'shortFormPart', 'items']
    datatype = "Enumeration"
    def __init__(self, node=None):
        self.name = None
        self.shortFormPart = None
        self.comment = None
        self.items = []
        if node is not None:
            self.parse(node)

    def parse(self, node):
        self.name = node.attrib['name']
        self.shortFormPart = node.attrib['shortFormPart']
        self.comment = node.attrib.get('comment', None)
        item_nodes = list(node)
        for item_node in item_nodes:
            self.items.append(MALEnumerationItemXML(item_node))


class MALErrorXML(object):
    __slots__ = ['name', 'number', 'comment']
    datatype = "Error"

    def __init__(self, node=None):
        self.name = None
        self.comment = None
        self.number = None
        if node is not None:
            self.parse(node)

    def parse(self, node):
        self.name = node.attrib['name']
        self.number = node.attrib['number']
        self.comment = node.attrib.get('comment', None)

def tag(name):
    return "{}{}".format('{'+MAL_NS+'}', name)


def parse_datatype(node):
    if node.tag == tag('fundamental') or node.tag == tag('attribute'):
        return MALElementXML(node)
    elif node.tag == tag('composite'):
        return MALCompositeXML(node)
    elif node.tag == tag('enumeration'):
        return MALEnumerationXML(node)
    else:
        raise RuntimeError("Unexpected node tag : {}".format (node.tag))

def parse_datatypes(node):
    datatypes_dict = {}
    for subnode in node:
        d = parse_datatype(subnode)
        dtype = d.datatype
        if dtype not in datatypes_dict:
            datatypes_dict[dtype] = dict()
        datatypes_dict[dtype][d.name] = d
    return datatypes_dict

def parse_services(node):
    pass

def parse_errors(node):
    error_dict = {}
    for subnode in node:
        d = MALErrorXML(subnode)
        error_dict[d.name] = d
    return error_dict

"""
Root {
    Area {
        services x N {
            DataTypes,}
        dataTypes {

        },
        errors {
            error xN
        }
    }
}
"""
root = ET.parse(MAL_FILE).getroot()


for area_node in list(root):
    if area_node.tag != tag('area'):
        raise RuntimeError("Expected an area")
    area = Area()
    area.name = area_node.attrib['name']
    area.number = area_node.attrib['number']
    area.version = area_node.attrib['version']

    if 'comment' in area_node.attrib:
        area.comment = area_node.attrib['comment']

    for area_subnode in list(area_node):
        if area_subnode.tag == tag('dataTypes'):
            data_types = parse_datatypes(area_subnode)
        elif area_subnode.tag == tag('errors'):
            error_dict = parse_errors(area_subnode)
        elif area_subnode.tag == tag('service'):
            parse_service(area_subnode)

    with open(PARAMFILE, 'r') as pf:
        parameters = yaml.load(pf, Loader=yaml.SafeLoader)
    typedict = parameters['typedict']
    ctrldict = parameters['controldict']

    with open(OUTFILE, 'w') as f:
        f.write("from enum import IntEnum\n")
        f.write("from abc import ABC\n")
        f.write("\n")
        f.write("name = \"{}\"\n".format(area.name))
        f.write("number = {}\n".format(area.number))
        f.write("version = {}\n".format(area.version))
        f.write("\n")

        f.write("class MALShortForm(IntEnum):\n")
        for dtype in data_types:
            for _, d in data_types[dtype].items():
                if d.shortFormPart:
                    f.write("    {} = {}\n".format(d.name.upper(), d.shortFormPart))

        f.write("\n")

        def write_element_class(d, blocks=[]):
            if d.extends is None:
                parentclass = 'ABC'
            elif d.extends.area == area.name:
                parentclass = d.extends.name
            else:
                parentclass = d.extends.area + '.' + d.extends.name

            f.write("class {}({}):\n".format(d.name, parentclass))
            f.write(4*' ' + '"""' + d.comment + '"""\n')
            f.write("\n")
            if d.shortFormPart:
                f.write(4*' ' + "shortForm = {}.{}\n".format("MALShortForm", d.name.upper()))
            else:
                f.write(4*' ' + "shortForm = None\n")
            if d.name in typedict:
                f.write(4*' ' + "value_type = {}\n".format(typedict[d.name]))

            if d.name in ctrldict:
                f.write("\n")
                minvalue = ctrldict[d.name][0]
                maxvalue = ctrldict[d.name][1]
                f.write(4*' ' + "def __init__(self, value):\n")
                f.write(8*' ' + "super().__init__(value)\n")
                f.write(8*' ' + "if type(value) == int and ( value < {} or value > {} ):\n".format(minvalue, maxvalue))
                f.write(12*' ' + "raise ValueError(\"Authorized value is between {} and {}.\")\n".format(minvalue, maxvalue))

            for b in blocks:
                f.write("\n")
                f.write(b)
            f.write("\n")
            f.write("\n")

        def write_enumeration_class(d):
            f.write("class {}({}):\n".format(d.name, "IntEnum"))
            f.write(4*' ' + '"""' + d.comment + '"""\n')
            f.write("\n")
            if d.shortFormPart:
                f.write(4*' ' + "shortForm = {}.{}\n".format("MALShortForm", d.name.upper()))
            else:
                f.write(4*' ' + "shortform = None\n")
            f.write('\n')
            for item in d.items:
                f.write(4*' ' + "{} = {}".format(item.value, item.nvalue))
                if item.comment is not None:
                    f.write(' # '+item.comment)
                f.write('\n')

            f.write("\n")
            f.write("\n")

        for dname, d in data_types['Enumeration'].items():
            write_enumeration_class(d)

        def write_error_class(d):
            f.write("class {}({}):\n".format("Errors", "IntEnum"))
            f.write(4*' ' + '""" All MAL errors."""\n')
            f.write("\n")

            for e in d:
                f.write(4*' ' + "{} = {}".format(e.name, e.number))
                if e.comment is not None:
                    f.write(' # '+e.comment)
                f.write('\n')

            f.write("\n")
            f.write("\n")

        write_error_class(error_dict.values())

        write_element_class(data_types['Element']['Element'])


        blockattribute = [
        "    def __init__(self, value):\n" +
        "        if type(value) == type(self):\n" +
        "            self._value = value.value\n" +
        "        elif type(value) == type(self).value_type:\n" +
        "            self._value = value\n" +
        "        else:\n" +
        "            raise TypeError(\"Expected {}, got {}.\".format(type(self).value_type, type(value)))\n"
        ,
        "    @property\n" +
        "    def value(self):\n" +
        "        return self._value\n",
        "    def copy(self):\n" +
        "        return self.value\n"
        ]
        write_element_class(data_types['Element']['Attribute'], blockattribute)

        blockcomposite = [
        "    @property\n" +
        "    def value(self):\n" +
        "        return self._value\n"
        ,
        "    def copy(self):\n" +
        "        value = []\n" +
        "        for v in self.value:\n" +
        "            if type(v) == list:\n" +
        "                value.append([x.copy() for x in v])\n" +
        "            else:\n" +
        "                value.append(v.copy())\n" +
        "        return self.__class__(value)\n"
        ]

        write_element_class(data_types['Element']['Composite'], blockcomposite)

        for dname, d in data_types['Element'].items():
            if dname == 'Element' or dname == 'Attribute' or dname == 'Composite':
                continue
            write_element_class(d)


        def write_composite_class(d, blocks=[]):
            if d.extends is None:
                parentclass = 'ABC'
            elif d.extends.area == area.name:
                parentclass = d.extends.name
            else:
                parentclass = d.extends.area + '.' + d.extends.name

            f.write("class {}({}):\n".format(d.name, parentclass))
            f.write(4*' ' + '"""' + d.comment + '"""\n')
            f.write("\n")
            if d.shortFormPart:
                f.write(4*' ' + "shortForm = {}.{}\n".format("MALShortForm", d.name.upper()))
            else:
                f.write(4*' ' + "shortForm = None\n")

            f.write("\n")

            f.write(4*' ' + "def __init__(self, value):\n")
            f.write(8*' ' + "if type(value) == type(self):\n")
            f.write(12*' ' + "self._value = value.copy()\n")
            f.write(8*' ' + "else:\n")
            for i, field in enumerate(d.fields):
                if field.maltype.area == area.name:
                    fieldtype = field.maltype.name
                else:
                    fieldtype = field.maltype.area + "." + f.maltype.name
                f.write(12*' ' + "self.{0} = value[{1}]\n".format(field.name, i))

            for i, field in enumerate(d.fields):
                f.write("\n")
                f.write(4*' ' + "@property\n")
                f.write(4*' ' + "def {}(self):\n".format(field.name))
                f.write(8*' ' + "return self._value[{}]\n".format(i))
                f.write("\n")
                f.write(4*' ' + "@{}.setter\n".format(field.name))
                f.write(4*' ' + "def {0}(self, {0}):\n".format(field.name))
                if field.maltype.isList:
                    f.write(8*' ' + "self._value[{0}] = [{1}(x) for x in {2}]\n".format(i, fieldtype, field.name))
                else:
                    f.write(8*' ' + "self._value[{0}] = {1}({2})\n".format(i, fieldtype, field.name))

            f.write("\n")
            f.write("\n")

        for dname, d in data_types['Composite'].items():
            write_composite_class(d)


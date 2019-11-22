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

class DataType(object):
    def __init__(self):
        self.datatype = None
        self.fundamental = False
        self.extends = None
        self.name = None
        self.comment = None
        self.shorfFormPart = None

def tag(name):
    return "{}{}".format('{'+MAL_NS+'}', name)

def parse_datatype(node):
    d = None
    if node.tag == tag('fundamental'):
        d = DataType()
        d.datatype = "Element"
        d.name = node.attrib['name']
        d.fundamental = True
        d.shortFormPart = None
        d.comment = node.attrib.get('comment', None)
        extend_nodes = list(node)
        if len(extend_nodes) > 0 and extend_nodes[0].tag == tag('extends'):
            type_node = list(extend_nodes[0])[0]
            d.extends = "{}.{}".format(type_node.attrib['area'], type_node.attrib['name'])
    elif node.tag == tag('attribute'):
        d = DataType()
        d.datatype = "Element"
        d.name = node.attrib['name']
        d.fundamental = False
        d.shortFormPart = node.attrib['shortFormPart']
        d.comment = node.attrib.get('comment', None)
        d.extends = "MAL.Attribute"
    elif node.tag == tag('composite'):
        pass
    elif node.tag == tag('enumeration'):
        pass
    else:
        raise RuntimeError("Unexpected node tag : {}".format (node.tag))
    return d

def parse_datatypes(root):
    datatypes_dict = {}
    for node in list(root):
        d = parse_datatype(node)
        if not d:
            continue
        dtype = d.datatype
        if dtype not in datatypes_dict:
            datatypes_dict[dtype] = dict()
        datatypes_dict[dtype][d.name] = d
    return datatypes_dict

def parse_services(root):
    pass

def parse_errors(root):
    pass

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
            parse_errors(area_subnode)
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

        f.write("class MAL_SHORTFORMS(IntEnum):\n")
        for dtype in data_types:
            for _, d in data_types[dtype].items():
                if d.shortFormPart:
                    f.write("    {} = {}\n".format(d.name.upper(), d.shortFormPart))

        f.write("\n")

        def write_element_class(d, blocks=[]):
            parentclass = d.extends or 'ABC'
            if '.' in parentclass and parentclass.split('.')[0] == area.name:
                parentclass = parentclass.split('.')[1]
            f.write("class {}({}):\n".format(d.name, parentclass))
            f.write(4*' ' + '"""' + d.comment + '"""\n')
            f.write("\n")
            if d.shortFormPart:
                f.write(4*' ' + "shortform = {}.{}\n".format("MAL_SHORTFORMS", d.name.upper()))
            else:
                f.write(4*' ' + "shortform = None\n")
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

        write_element_class(data_types['Element']['Element'])

        blockattribute = [
        "    def __init__(self, value):\n" +
        "        if type(value) == type(self):\n" +
        "            self._value = value.value\n" +
        "        elif type(value) == type(self).value_type:\n" +
        "            self._value = value\n" +
        "        else:\n" +
        "            raise TypeError(\"Expected {}, got {}.\".format(type(self).value_type, type(value)))\n",
        "    @property\n" +
        "    def value(self):\n" +
        "        return self._value\n"
        ]
        write_element_class(data_types['Element']['Attribute'], blockattribute)

        for dname, d in data_types['Element'].items():
            if dname == 'Element' or dname == 'Attribute':
                continue
            write_element_class(d)

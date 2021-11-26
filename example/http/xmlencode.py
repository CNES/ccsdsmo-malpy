#! /bin/python3

import sys
sys.path.append('../../src/')


from malpy.mo import mal
from malpy.mo.mc.services import parameter
from malpy import encoding

#encoding.LOG_LEVEL = 'DEBUG'

m = mal.Subscription(
    ["MySubscription",
        [
            [
                ['Id1', 'Id2', None],
                True,
                True,
                True,
                True,
                [
                    ["IDK1", 9, None, None],
                    None
                ]
            ]
        ]
    ]
    )


u = mal.UpdateHeader(
    [
        123456.0,
        "http://localhost:80",
        mal.UpdateTypeEnum.CREATION,
        ["IDK1", 9, 1, 3]
    ])

ul = mal.UpdateHeaderList(
    [
        [
            123456.0,
            "http://localhost:80",
            mal.UpdateTypeEnum.CREATION,
            ["IDK1", 9, 1, 3]
        ],
        [
            789011.0,
            "http://localhost:443",
            mal.UpdateTypeEnum.CREATION,
            ["IDK2", 8, 8, 2]
	]
    ])

p= parameter.ParameterValue([mal.UOctet(5), mal.Blob(b'toto'), mal.String("Toto")])

print("mllml", p._internal_value[2]._isNull)

e = encoding.XMLEncoder()

em = e.encode_body([m])
print(e.decode_body(em))
print("{}".format(em.decode('utf-8')))
eu = e.encode_body([u])
print(e.decode_body(eu))
print("{}".format(eu.decode('utf-8')))
eul = e.encode_body([ul,u])
deul = e.decode_body(eul)
print(eul.decode('utf8'))
print(deul)

coded  = e.encode_body([p])
print(coded.decode('utf8'))
decoded = e.decode_body(coded)
print(decoded[0].internal_value[1].internal_value)
print(e.encode_body(decoded).decode('utf8'))

import time
p = parameter.ParameterValueDetailsList([
    parameter.ParameterValueDetails([ 2, 2, time.time(), [mal.UOctet(0),mal.Long(1),None]])])
pc = e.encode_body([p])
print(pc.decode('utf8'))

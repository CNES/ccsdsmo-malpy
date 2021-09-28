#! /bin/python3

import sys
sys.path.append('../../src/')


from mo import mal
from mo.mc.services import parameter
import encoding

encoding.LOG_LEVEL = 'DEBUG'

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
        ["IDK1", 9, None, None]
    ])

ul = mal.UpdateHeaderList(
    [
        [
            123456.0,
            "http://localhost:80",
            mal.UpdateTypeEnum.CREATION,
            ["IDK1", 9, None, None]
        ],
        [
            789011.0,
            "http://localhost:443",
            mal.UpdateTypeEnum.CREATION,
            ["IDK2", 8, None, None]
	]
    ])

parameter = parameter.ParameterValue([mal.UOctet(5), mal.Blob(b'toto'), mal.String("Toto")])

e = encoding.XMLEncoder()

em = e.encode_body([m])
print(e.decode_body(em))
# print("{}".format(em.decode('utf-8')))
eu = e.encode_body([u])
print(e.decode_body(eu))
# print("{}".format(eu.decode('utf-8')))
eul = e.encode_body([ul,u])
deul = e.decode_body(eul)
print(deul)

coded  = e.encode_body([parameter])
print(coded.decode('utf8'))
decoded = e.decode_body(coded)
print(decoded[0].internal_value[1].internal_value)
print(e.encode_body(decoded).decode('utf8'))

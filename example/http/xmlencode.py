#! /bin/python

import sys
sys.path.append('../../src/')


from mo import mal
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
        [123456.0,
	 "http://localhost:80",
	 mal.UpdateTypeEnum.CREATION,
	 ["IDK1", 9, None, None]
	 ]
	 )

ul = mal.UpdateHeaderList(
    [
        [123456.0,
	 "http://localhost:80",
	 mal.UpdateTypeEnum.CREATION,
	 ["IDK1", 9, None, None]
	 ],
        [789011.0,
	 "http://localhost:443",
	 mal.UpdateTypeEnum.CREATION,
	 ["IDK2", 8, None, None]
	 ]
    ]
    )


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


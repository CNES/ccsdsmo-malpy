#! /bin/python3

import logging
import sys
sys.path.append('../../src')

from malpy.mo import mal, mpd
from malpy.mo.mpd.services import ordermanagement, productorderdelivery

from malpy.transport import http
from malpy import encoding

TRANSPORT_CONF = {}
def entity2uri_function(entity, area=0, service=0,version=0):
    return TRANSPORT_CONF["{}@{}@{}@{}".format(version,service,area,entity)]
http.set_entity2uri_function(entity2uri_function)

logging.basicConfig(level=logging.INFO)


def updateTransportConf(handler, URI):
    global TRANSPORT_CONF
    TRANSPORT_CONF["{}@{}@{}@{}".format(handler.AREA_VERSION,handler.SERVICE,handler.AREA,handler.provider_entity)] = URI

def main():

    # PROVIDER
    host = '127.0.0.1'
    port = 1443
    private_port = 1445

    provider = "myprovider"
    #consumer = "CNES-Olivier"
    consumer = "malhttp://127.0.0.1:1444/test/value_{}_{}".format(host, private_port)

    s = http.HTTPSocket(use_https=False)
    enc = encoding.XMLEncoder()
    request = ordermanagement.SubmitStandingOrderConsumerHandler(s, enc, consumer_entity=consumer, provider_entity=provider)
    updateTransportConf(request, 'malhttp://127.0.0.1:1443/OrderManagement')
    request.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    request.request([mpd.StandingOrder([mal.Identifier("Olivier"), None, None,
                                        mpd.DeliveryMethodEnumEnum.SERVICE, None, mal.String("A comment")
                                        ])
                    ])
    message = request.receive_response()
    print("[*] The returned identifier is '{}'".format(message.msg_parts[0]._internal_value))

    s2 = http.HTTPSocket(use_https=False, private_host=host, private_port=private_port)

    subscriber = productorderdelivery.DeliverProductsConsumerHandler(s2, enc, consumer_entity=consumer, provider_entity=provider)
    updateTransportConf(subscriber, 'malhttp://127.0.0.1:1443/ProductOrderDeliveryInternalBroker')
    subscriber.register(mal.Subscription( [mal.Identifier("Olivier"), [], [], []]))
    message = subscriber.receive_register_ack()
    print(message.msg_parts)

    while True:
        notification = subscriber.receive_notify()
        print("[*] DeliverProduct received: {}".format(notification.msg_parts[-1][-1]._internal_value))

if __name__ == "__main__":
    main()

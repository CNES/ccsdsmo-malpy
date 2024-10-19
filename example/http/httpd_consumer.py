#!/usr/bin/env python3

import http.server
import http.client
import io
import logging
import os.path
import pickle
import socket
from struct import *
import sys

sys.path.append('../../src')

from malpy.mo import mal

# HTTPD CONSUMER URI
HOST = '127.0.0.1'
PORT = 1444

server_address = (HOST, PORT)

#FORMAT = config['LOGGER_FORMAT']
logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)

sockets_list = {}

class MyTestHandler(http.server.BaseHTTPRequestHandler):

    struct_format = '!I'

    def _split_uri(self, uri):
        logger = logging.getLogger(__name__)

        host = None
        port = None
        path = None

        splitted_uri = uri.split(':')
        if splitted_uri[0][:4].lower() == "http":
            host = splitted_uri[1][2:]
            rest_uri = uri.split(':',2)[2]
        else:
            host = splitted_uri[0]
            rest_uri = uri.split(':',1)[1]

        splitted_rest_uri = rest_uri.split('/',1)
        port = splitted_rest_uri[0]
        if len(splitted_rest_uri) > 1:
            path = splitted_rest_uri[1]

        logger.debug('uriparsed {} host {} port {} path {}'.format(uri, host, port, path))

        return (host,port,path)

    def _split_path(self, path):
        logger = logging.getLogger(__name__)

        splitted_path = path.split('_')
        host = splitted_path[1]
        port = splitted_path[2]
        logger.debug('path {} host {} port {}'.format(path, host, port))

        return (host, port)

    def send_to_consumer(self, s, headers, body):
        logger = logging.getLogger(__name__)

        request_dict= {
            "headers": headers,
            "body": body
        }

        # Encode data
        data=pickle.dumps(request_dict)
        data_lenght = len(data)
        data_lenght_packed = pack(self.struct_format,data_lenght)

        # Send data lenght
        logger.debug("Send {} bytes '{}'".format(len(data_lenght_packed),data_lenght_packed))
        s.send(data_lenght_packed)

        # Send data
        logger.debug("Send {} bytes '{}'".format(data_lenght,data))
        s.send(data)

    def do_GET(self):
        logger = logging.getLogger(__name__)

        logger.debug("Request: {}".format(self.requestline) )
        logger.debug("Headers: {}".format(self.headers) )
        content_length = self.headers.get('Content-Length')
        if content_length:
            logger.info("Data: {}".format(self.rfile.read(int(content_length))) )
        self.send_response(404, 'Get is not supported')
        self.end_headers()
        self.wfile.write("<html><h1>Only POST request are authorized</h1><p>{}</html>".format(self.requestline).encode('utf-8'))

    def do_POST(self):
        logger = logging.getLogger(__name__)

        # Receive headers and body from provider
        logger.info(" ******************** Receive request from provider (Public request) **********************")
        logger.debug("Request: {}".format(self.requestline))
        logger.debug("Headers: {}".format(self.headers))
        content_length = self.headers.get('Content-Length')
        if content_length:
            body = self.rfile.read(int(content_length))
            logger.debug("Body: {}".format(body) )
        else:
            body = ""
            logger.info("Data: None")

        logger.info("headers : {}\nbody : {}".format(self.headers,body.decode('utf-8')))

        # Get consumer_host and port from URI requestline
        uri_path = self.requestline.split(' ')[1]
        #logger.debug("uri_host {} uri_port {} uri_path {}".format(uri_host, uri_port, uri_path))
        consumer_host, consumer_port = self._split_path(uri_path)
        logger.debug("consumer_host {} consumer_port {}".format(consumer_host, consumer_port))

        key = "{}:{}".format(consumer_host, consumer_port)
        # Search key in openned connections
        if key in sockets_list:
            s = sockets_list[key]
        else:
            # Create and connect socket to consumer
            s = socket.socket()
            s.connect((consumer_host, int(consumer_port)))
            logger.info("[*] Connected to {} {}".format(consumer_host, consumer_port))
            sockets_list[key] = s
            logger.debug("Sockets_list {}".format(sockets_list))

        # Send to Consumer
        logger.info(" ******************** Send data to consumer (private) **********************")
        try:
            data_sent = self.send_to_consumer(s, self.headers, body)
        except Exception as e:
            logger.warning("Send to consumer {} Exception {}".format(key, e))
            data_sent = 0


        if data_sent == 0:
            try:
                # Try to create a new socket
                s = socket.socket()
                logger.info("[*] Try to reconnect to {} {}".format(consumer_host, consumer_port))
                s.connect((consumer_host, int(consumer_port)))
                sockets_list[key] = s
                logger.debug("Sockets_list {}".format(sockets_list))
                data_sent = self.send_to_consumer(s, self.headers, body)
                logger.info("[*] Send to {} {} Success".format(consumer_host, consumer_port))
            except Exception as e:
                logger.warning("Send to consumer {} Abort Exception {}".format(key, e))


        # TODO Revoir ce if ..... Remove socket in sockets_list except for PROGRESS_UPDATE and PUBSUB_NOTIFY stage
        if (self.headers.get('X-MAL-Interaction-Stage') != str(mal.MAL_INTERACTION_STAGES.PROGRESS_UPDATE) and \
            (self.headers.get('X-MAL-Interaction-Stage') != str(mal.MAL_INTERACTION_STAGES.PUBSUB_NOTIFY)) ):
           sockets_list.pop(key)

        logger.info("********** Send Http Response to provider (Public) ************************")
        self.send_response(200, 'OK')
        self.end_headers()
        self.wfile.write(b'')


with http.server.HTTPServer(server_address, MyTestHandler) as httpd:

   # httpd.socket = context.wrap_socket(httpd.socket,
   #                                server_side=True)
    logger.info("serving at port {}".format(PORT))
    httpd.serve_forever()

import socket
from ipaddress import ip_address

import requests

from django.conf import settings
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def get_publisher():
    """
    get a list of all publishers
    """
    req = requests.get(
        'http://{}:{}/api/v1/clients/'.format(settings.SRS_IP,
                                              settings.SRS_API_PORT)).json()
    publisher = []

    for client in req['clients']:
        if client['publish']:
            publisher.append(client)

    return publisher


def kick_streams():
    """
    check if low priority stream is running and when is true kick them out
    """
    for client in get_publisher():
        stream = client['url'].split('/')[-1]

        if stream == settings.LOW_PRIORITY_STREAM:
            requests.delete(
                'http://{}:{}/api/v1/clients/{}'.format(settings.SRS_IP,
                                                        settings.SRS_API_PORT,
                                                        client['id']))

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((settings.SOCKET_IP, settings.SOCKET_PORT))

            try:
                sock.sendall(b'stop')
            finally:
                sock.close()


def start_stream(last):
    """
    when last unpublished stream was the high priority stream,
    start the ffplayout-engine
    """
    if last == settings.HIGH_PRIORITY_STREAM:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((settings.SOCKET_IP, settings.SOCKET_PORT))

        try:
            sock.sendall(b'start')
        finally:
            sock.close()


class Publish(APIView):
    """
    srs communication with the API
    endpoint: http://127.0.0.1:8001/api/srs/publish/?key=1234abc
    """
    permission_classes = (AllowAny,)
    parser_classes = [JSONParser]

    def get(self, request, *args, **kwargs):
        if 'status' in request.GET.dict():
            return Response(status=204)
        else:
            return Response(status=404)

    def post(self, request, *args, **kwargs):
        # check api auth
        if request.query_params['key'] != settings.SRS_KEY:
            return Response({"code": 403, "data": None})
        elif request.data['action'] == 'on_publish':
            # check rtmp auth and private IP
            if self.rtmp_key(request.data) or \
                    ip_address(request.data['ip']).is_private:
                return self.check_streams(request.data)
            else:
                return Response({"code": 403, "data": None})
        elif request.data['action'] == 'on_unpublish':
            start_stream(request.data['stream'])
            return Response({"code": 0, "data": None})
        else:
            return Response({"code": 200, "data": None})

    def check_streams(self, data):
        if data['stream'] == settings.HIGH_PRIORITY_STREAM:
            kick_streams()
        elif data['stream'] == settings.LOW_PRIORITY_STREAM:
            for client in get_publisher():
                stream = client['url'].split('/')[-1]

                if stream == settings.HIGH_PRIORITY_STREAM:
                    return Response({"code": 403, "data": None})

        return Response({"code": 0, "data": None})

    def rtmp_key(self, req):
        param = req['param'].lstrip('?')
        params = param.split('&')
        obj = {}

        if params:
            for param in params:
                key, value = param.split('=')
                obj[key] = value

            if 'key' in obj and obj['key'] == settings.RTMP_KEY:
                return True

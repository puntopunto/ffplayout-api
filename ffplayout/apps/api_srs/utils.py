import socket

import requests

from django.conf import settings


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

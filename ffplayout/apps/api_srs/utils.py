import re

import requests
from apps.api_player.utils import SystemControl
from django.conf import settings


def get_publisher():
    """
    get a list of all publishers
    """
    publisher = []
    req = requests.get(
        'http://{}:{}/api/v1/clients/'.format(settings.SRS_IP,
                                              settings.SRS_API_PORT)).json()

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
        suffix = re.findall(r'\d{3}', client['url'])
        engine = f'engine-{suffix}' if suffix else 'engine-001'

        if stream == settings.LOW_PRIORITY_STREAM:
            requests.delete(
                'http://{}:{}/api/v1/clients/{}'.format(settings.SRS_IP,
                                                        settings.SRS_API_PORT,
                                                        client['id']))

            SystemControl('stop', engine)


def start_stream(last):
    """
    when last unpublished stream was the high priority stream,
    start the ffplayout-engine

    LIMITATION: for now only first engine-001 can be startet
    """
    if last == settings.HIGH_PRIORITY_STREAM:
        SystemControl('start', 'engine-001')

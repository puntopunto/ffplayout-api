from threading import Thread

import zmq
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import GuiSettings, MessengePresets


class MessagePresetTests(APITestCase):
    """
    test messager, save/get/update/delete preset
    """

    def setUp(self):
        """
        set defaults
        """
        self.user = User.objects.create_user('john', 'john@snow.com',
                                             'johnpassword')
        self.client.login(username='john', password='johnpassword')

        self.preset_obj = {
            'name': 'Preset1',
            'message': 'hello from ffplayout...',
            'x': '10',
            'y': '400',
            'font_size': 36,
            'font_spacing': 3,
            'font_color': '#0000ff',
            'font_alpha': .95,
            'show_box': True,
            'box_color': '#005511',
            'box_alpha': 0.55,
            'border_width': 2,
            'overall_alpha': '1.0'
        }

        self.preset = MessengePresets.objects.create(**self.preset_obj)

    def test_create_message_preset(self):
        """
        Ensure we can create a message preset.
        """

        self.preset_obj['name'] = 'Preset2'
        self.preset_obj['message'] = 'how are you?'

        response = self.client.post('/api/player/messenger/',
                                    self.preset_obj, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MessengePresets.objects.count(), 2)
        self.assertEqual(MessengePresets.objects.get(id=2).name, 'Preset2')

    def test_read_message_preset(self):
        """
        Ensure we can read a message preset.
        """

        self.preset_obj['id'] = 1

        response = self.client.get('/api/player/messenger/1/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), self.preset_obj)
        self.assertEqual(response.json()['name'], 'Preset1')

    def test_update_message_preset(self):
        """
        Ensure we can update a message preset.
        """

        self.preset_obj['id'] = 1
        self.preset_obj['name'] = 'Preset2.1'
        self.preset_obj['message'] = 'new update...'

        response = self.client.put('/api/player/messenger/1/',
                                   self.preset_obj, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), self.preset_obj)
        self.assertEqual(response.json()['name'], 'Preset2.1')

    def test_delete_message_preset(self):
        """
        Ensure we can delete a message preset.
        """

        response = self.client.delete('/api/player/messenger/1/',
                                      format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


def zmq_server():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://127.0.0.1:5555")

    # message = socket.recv()
    # print(f'Received request: {message}')
    socket.recv()
    socket.send(b'0 Success')


class SendMessageTests(APITestCase):
    """
    test message sending
    """

    def setUp(self):
        self.server = Thread(target=zmq_server)
        self.server.start()

        self.message = {
            'text': 'hello from ffplayout...',
            'x': '10',
            'y': '400',
            'fontsize': 36,
            'line_spacing': 3,
            'fontcolor': '#0000ff',
            'box': True,
            'boxcolor': '#005511',
            'boxborderw': 2,
            'alpha': '1.0'
        }

        self.user = User.objects.create_user('john', 'john@snow.com',
                                             'johnpassword')
        self.client.login(username='john', password='johnpassword')

        self.config = GuiSettings.objects.create(
            playout_config='/etc/ffplayout/ffplayout.yml'
        )

    def test_send_message(self):
        """
        send message to server
        """
        response = self.client.post('/api/player/send/message/',
                                    {'data': self.message, 'channel': 1},
                                    format='json')

        self.assertEqual(response.json()['status'], {'Success': '0 Success'})

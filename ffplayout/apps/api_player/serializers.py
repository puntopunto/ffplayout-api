import configparser
import os
from shutil import copyfile

from apps.api_player.models import GuiSettings, MessengePresets
from apps.api_player.utils import read_yaml, write_yaml
from django.contrib.auth.models import User
from rest_framework import serializers


def create_engine_config(_path, yml_config):
    suffix = os.path.basename(_path).split('-')[1].split('.')[0]
    config = configparser.ConfigParser()
    config.read('/etc/ffplayout/supervisor/conf.d/engine-001.conf')
    items = config.items('program:engine-001')

    config.add_section(f'program:engine-{suffix}')

    for (key, value) in items:
        if key == 'command':
            value = f'./venv/bin/python3 ffplayout.py -c {yml_config}'
        config.set(f'program:engine-{suffix}', key, value)

    config.remove_section('program:engine-001')

    with open(_path, 'w') as file:
        config.write(file)


class UserSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, required=False)
    old_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'old_password',
                  'new_password', 'email']

    def update(self, instance, validated_data):
        instance.password = validated_data.get('password', instance.password)

        if 'new_password' in validated_data and \
                'old_password' in validated_data:
            if not validated_data['new_password']:
                raise serializers.ValidationError(
                    {'new_password': 'not found'})

            if not validated_data['old_password']:
                raise serializers.ValidationError(
                    {'old_password': 'not found'})

            if not instance.check_password(validated_data['old_password']):
                raise serializers.ValidationError(
                    {'old_password': 'wrong password'})

            if validated_data['new_password'] and \
                    instance.check_password(validated_data['old_password']):
                # instance.password = validated_data['new_password']
                instance.set_password(validated_data['new_password'])
                instance.save()
                return instance
        elif 'email' in validated_data:
            instance.email = validated_data['email']
            instance.save()
            return instance
        return instance


class GuiSettingsSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        if not os.path.isfile(validated_data['engine_service']):
            create_engine_config(validated_data['engine_service'],
                                 validated_data['playout_config'])
        if not os.path.isfile(validated_data['playout_config']):
            suffix = os.path.basename(
                validated_data['playout_config']).split('-')[1].split('.')[0]
            yaml_obj = read_yaml('/etc/ffplayout/ffplayout-001.yml')
            old_log_path = yaml_obj['logging']['log_path'].rstrip('/')
            old_pls_path = yaml_obj['playlist']['path'].rstrip('/')

            if os.path.basename(old_log_path) == 'ffplayout':
                log_path = f'{old_log_path}/channel-{suffix}'
            else:
                log_path = f'{os.path.dirname(old_log_path)}/channel-{suffix}'

            if os.path.basename(old_pls_path) == 'playlists':
                play_path = f'{old_pls_path}/channel-{suffix}'
            else:
                play_path = f'{os.path.dirname(old_pls_path)}/channel-{suffix}'

            yaml_obj['logging']['log_path'] = log_path
            yaml_obj['playlist']['path'] = play_path

            if not os.path.isdir(log_path):
                os.makedirs(log_path, exist_ok=True)

            if not os.path.isdir(play_path):
                os.makedirs(play_path, exist_ok=True)

            write_yaml(yaml_obj, validated_data['playout_config'])

        settings = GuiSettings.objects.create(**validated_data)

        return settings

    def update(self, instance, validated_data):
        if not os.path.isfile(validated_data['engine_service']):
            create_engine_config(validated_data['engine_service'],
                                 validated_data['playout_config'])
        if not os.path.isfile(validated_data['playout_config']):
            copyfile('/etc/ffplayout/ffplayout-001.yml',
                     validated_data['playout_config'])

        instance.channel = validated_data.get('channel', instance.channel)
        instance.player_url = validated_data.get('player_url',
                                                 instance.player_url)
        instance.playout_config = validated_data.get('playout_config',
                                                     instance.playout_config)
        instance.engine_service = validated_data.get('engine_service',
                                                     instance.engine_service)
        instance.net_interface = validated_data.get('net_interface',
                                                    instance.net_interface)
        instance.media_disk = validated_data.get('media_disk',
                                                 instance.media_disk)
        instance.save()
        return instance

    class Meta:
        model = GuiSettings
        fields = '__all__'


class MessengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessengePresets
        fields = '__all__'

import configparser
import os
from shutil import copyfile

from apps.api_player.models import GuiSettings, MessengePresets
from django.contrib.auth.models import User
from rest_framework import serializers


def create_engine_config(path, yml_config):
    digit = os.path.basename(path).split('-')[1].split('.')[0]
    config = configparser.ConfigParser()
    config.read('/etc/ffplayout/supervisor/conf.d/engine-001.conf')
    items = config.items('program:engine-001')

    config.add_section(f'program:engine-{digit}')

    for (key, value) in items:
        if key == 'command':
            value = f'./venv/bin/python3 ffplayout.py -c {yml_config}'
        config.set(f'program:engine-{digit}', key, value)

    config.remove_section('program:engine-001')

    with open(path, 'w') as file:
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
            copyfile('/etc/ffplayout/ffplayout-001.yml',
                     validated_data['playout_config'])

        settings = GuiSettings.objects.create(**validated_data)

        return settings

    def update(self, instance, validated_data):
        if not os.path.isfile(validated_data['engine_service']):
            create_engine_config(validated_data['engine_service'],
                                 validated_data['playout_config'])
        if not os.path.isfile(validated_data['playout_config']):
            copyfile('/etc/ffplayout/ffplayout-001.yml',
                     validated_data['playout_config'])

        return instance

    class Meta:
        model = GuiSettings
        fields = '__all__'


class MessengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessengePresets
        fields = '__all__'

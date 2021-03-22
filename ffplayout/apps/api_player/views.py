import os
import shutil
from time import sleep
from urllib.parse import unquote

from apps.api_player.models import GuiSettings, MessengePresets
from apps.api_player.serializers import (GuiSettingsSerializer,
                                         MessengerSerializer, UserSerializer)
from django.conf import settings
from django.contrib.auth.models import User
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.parsers import FileUploadParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .utils import (EngineControlSocket, SystemControl, SystemStats,
                    get_media_path, read_json, read_log, read_yaml,
                    send_message, write_json, write_yaml)


class CurrentUserView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserFilter(filters.FilterSet):

    class Meta:
        model = User
        fields = ['username']


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserFilter


class GuiSettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows media to be viewed.
    """
    queryset = GuiSettings.objects.all()
    serializer_class = GuiSettingsSerializer

    def destroy(self, request, *args, **kwargs):
        obj = GuiSettings.objects.get(id=kwargs['pk'])
        service_name = os.path.basename(obj.engine_service).split('.')[0]

        if os.path.isfile(obj.engine_service):
            os.remove(obj.engine_service)
        if os.path.isfile(obj.playout_config):
            os.remove(obj.playout_config)

        if settings.USE_SOCKET:
            engine = EngineControlSocket()
            engine.get_process(service_name)
            engine.stop()
            count = 0

            while engine.status().lower() != 'stopped' and count < 10:
                sleep(0.5)
                count += 1

            if engine.status().lower() == 'stopped':
                engine.remove_process(service_name)

        return super(
            GuiSettingsViewSet, self).destroy(request, *args, **kwargs)


class MessengerFilter(filters.FilterSet):

    class Meta:
        model = MessengePresets
        fields = ['name']


class MessengerViewSet(viewsets.ModelViewSet):
    queryset = MessengePresets.objects.all()
    serializer_class = MessengerSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MessengerFilter


class MessageSender(APIView):
    """
    send messages with zmq to the playout engine
    """

    def post(self, request, *args, **kwargs):
        if 'data' in request.data:
            response = send_message(request.data['data'])
            return Response({"success": True, 'status': response})

        return Response({"success": False})


class Config(APIView):
    """
    read and write config from ffplayout engine
    for reading endpoint is: http://127.0.0.1:8000/api/player/config/?config
    """
    parser_classes = [JSONParser]

    def get(self, request, *args, **kwargs):
        if 'configPlayout' in request.GET.dict():
            path = request.GET.dict()['path']
            yaml_input = read_yaml(path)

            if yaml_input:
                return Response(yaml_input)
            else:
                return Response(status=204)
        else:
            return Response(status=404)

    def post(self, request, *args, **kwargs):
        if 'data' in request.data and 'path' in request.query_params:
            write_yaml(request.data['data'], request.query_params['path'])
            return Response(status=200)

        return Response(status=404)


class SystemCtl(APIView):
    """
    controlling the ffplayout-engine over systemd services,
    or over a socket connecting
    """

    def post(self, request, *args, **kwargs):
        if 'run' in request.data:
            if settings.USE_SOCKET:
                control = SystemControl(request.data['run'],
                                        request.data['engine'])
            else:
                control = SystemControl(request.data['run'])

            if isinstance(control, int):
                return Response(status=control)
            else:
                return Response(control)

        return Response(status=404)


class LogReader(APIView):
    def get(self, request, *args, **kwargs):
        if 'type' in request.GET.dict() and 'date' in request.GET.dict():
            type = request.GET.dict()['type']
            _date = request.GET.dict()['date']
            config_path = request.GET.dict()['config_path']

            log = read_log(type, _date, config_path)

            if log:
                return Response({'log': log})
            else:
                return Response(status=204)
        else:
            return Response(status=404)


class Playlist(APIView):
    """
    read and write config from ffplayout engine
    for reading endpoint:
        http://127.0.0.1:8000/api/player/playlist/?date=2020-04-12
    """

    def get(self, request, *args, **kwargs):
        if 'date' in request.GET.dict():
            date = request.GET.dict()['date']
            config_path = request.GET.dict()['config_path']
            json_input = read_json(date, config_path)

            if json_input:
                return Response(json_input)
            else:
                return Response({
                    "success": False,
                    "error": "Playlist from {} not found!".format(date)})
        else:
            return Response(status=400)

    def post(self, request, *args, **kwargs):
        if 'data' in request.data:
            if 'config_path' in request.data:
                return write_json(request.data['data'],
                                  request.data['config_path'])
            if 'delete' in request.data['data']:
                if os.path.isfile(request.data['data']['delete']):
                    os.remove(request.data['data']['delete'])

                return Response(status=200)

        return Response({'detail': 'Unspecified save error'}, status=400)


class Statistics(APIView):
    """
    get system statistics: cpu, ram, etc.
    for reading, endpoint is: http://127.0.0.1:8000/api/player/stats/?stats=all
    """

    def get(self, request, *args, **kwargs):
        stats = SystemStats()
        if 'stats' in request.GET.dict() and request.GET.dict()['stats'] \
                and hasattr(stats, request.GET.dict()['stats']):
            return Response(
                getattr(stats, request.GET.dict()['stats'])())
        else:
            return Response(status=404)


class Media(APIView):
    """
    get folder/files tree, for building a file explorer
    for reading, endpoint is: http://127.0.0.1:8000/api/player/media/?path
    """

    def get(self, request, *args, **kwargs):
        if 'extensions' in request.GET.dict():
            extensions = request.GET.dict()['extensions']
            config_path = request.GET.dict()['config_path']

            if 'path' in request.GET.dict() and request.GET.dict()['path']:
                return Response({'tree': get_media_path(
                    extensions, config_path, request.GET.dict()['path']
                )})
            elif 'path' in request.GET.dict():
                return Response({'tree': get_media_path(extensions,
                                                        config_path)})
            else:
                return Response(status=204)
        else:
            return Response(status=404)


class FileUpload(APIView):
    parser_classes = [FileUploadParser]

    def put(self, request, filename, format=None):
        root = read_yaml(
            request.query_params['config_path'])['storage']['path']
        file_obj = request.data['file']
        filename = unquote(filename)
        path = unquote(request.query_params['path']).split('/')[1:]

        with open(os.path.join(root, *path, filename), 'wb') as outfile:
            for chunk in file_obj.chunks():
                outfile.write(chunk)
        return Response(status=204)


class FileOperations(APIView):

    def delete(self, request, *args, **kwargs):
        if 'file' in request.GET.dict() and 'path' in request.GET.dict():
            config_path = request.GET.dict()['config_path']
            root = read_yaml(config_path)['storage']['path']
            _file = unquote(request.GET.dict()['file'])
            folder = unquote(request.GET.dict()['path']).lstrip('/')
            _path = os.path.join(*(folder.split(os.path.sep)[1:]))
            fullPath = os.path.join(root, _path)

            if not _file or _file == 'null':
                if os.path.isdir(fullPath):
                    shutil.rmtree(fullPath, ignore_errors=True)
                    return Response(status=200)
                else:
                    return Response(status=404)
            elif os.path.isfile(os.path.join(fullPath, _file)):
                os.remove(os.path.join(fullPath, _file))
                return Response(status=200)
            else:
                return Response(status=404)
        else:
            return Response(status=404)

    def post(self, request, *args, **kwargs):
        if 'folder' in request.data and 'path' in request.data:
            config_path = request.data['config_path']
            root = read_yaml(config_path)['storage']['path']
            folder = request.data['folder']
            _path = request.data['path'].split(os.path.sep)
            _path = '' if len(_path) == 1 else os.path.join(*_path[1:])
            fullPath = os.path.join(root, _path, folder)

            try:
                # TODO: check if folder exists
                os.mkdir(fullPath)
                return Response(status=200)
            except OSError:
                Response(status=500)
        else:
            return Response(status=404)

    def patch(self, request, *args, **kwargs):
        if 'path' in request.data and 'oldname' in request.data \
                and 'newname' in request.data:
            config_path = request.data['config_path']
            root = read_yaml(config_path)['storage']['path']
            old_name = request.data['oldname']
            new_name = request.data['newname']
            _path = os.path.join(
                *(request.data['path'].split(os.path.sep)[2:]))
            old_file = os.path.join(root, _path, old_name)
            new_file = os.path.join(root, _path, new_name)

            os.rename(old_file, new_file)

            return Response(status=200)
        else:
            return Response(status=204)

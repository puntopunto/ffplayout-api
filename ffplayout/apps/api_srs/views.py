from django.conf import settings
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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
            # check rtmp auth
            if self.rtmp_key(request.data):
                print(request.data)
                if 'run' in request.data:
                    pass
                return Response({"code": 0, "data": None})
            else:
                return Response({"code": 403, "data": None})
        elif request.data['action'] == 'on_unpublish':
            # TODO: do something on unpublish
            return Response({"code": 0, "data": None})
        else:
            return Response({"code": 200, "data": None})

    def rtmp_key(self, req):
        param = req["param"].lstrip('?')
        params = param.split('&')
        obj = {}

        if params:
            for param in params:
                key, value = param.split('=')
                obj[key] = value

            if 'key' in obj and obj['key'] == settings.RTMP_KEY:
                return True

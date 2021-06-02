from ipaddress import ip_address

from django.conf import settings
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .utils import check_streams, rtmp_key, start_stream


# pylint: disable=unused-argument
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

        return Response(status=404)

    def post(self, request, *args, **kwargs):
        # check api auth
        if request.query_params['key'] != settings.SRS_KEY:
            return Response({"code": 403, "data": None})
        if request.data['action'] == 'on_publish':
            # check rtmp auth and private IP
            if rtmp_key(request.data) or \
                    ip_address(request.data['ip']).is_private:
                return check_streams(request.data)
            return Response({"code": 403, "data": None})
        if request.data['action'] == 'on_unpublish':
            start_stream(request.data['stream'])
            return Response({"code": 0, "data": None})

        return Response({"code": 200, "data": None})

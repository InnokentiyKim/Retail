from django.core.exceptions import ValidationError
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
import yaml


class AddGoods(APIView):
    def post(self, request: Request, *args, **kwargs):
        url = request.data.get('url', None)
        if url is None:
            return JsonResponse({'error': 'url is required'}, status=400)
        validate_url = URLValidator(verify_exists=True)
        try:
            validate_url(url)
        except ValidationError:
            return JsonResponse({'error': 'url is invalid'}, status=400)
        stream = get(url).content
        products_data = yaml.safe_load(stream)



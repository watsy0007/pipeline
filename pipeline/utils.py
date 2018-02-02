import requests
import sys
import traceback
import json
import hashlib
from urllib import parse
from scrapy.utils.project import get_project_settings


# error_handler
# args:
#   type: EXCHANGE_ERROR, EXCHANGE_QUEUE_ERROR, API_ERROR, PARSE_ERROR
#   kwargs: { exchange_name: '',
#               currency_name: '',
#               url: '',
#               request: json,
#               response: json,
#               file_name: '',
#               line: '',
#               error_message: ''  }
def error_handler(monitor_type, kwargs):
    kwargs['monitor_type'] = monitor_type
    requests.post(get_project_settings().get('ERROR_COLLECTION_URL'), data=kwargs, headers={'Connection':'close'})


def spider_error(kwargs):
    error_handler('SPIDER_ERROR', kwargs)


def api_error(kwargs):
    error_handler('API_ERROR', kwargs)


def parse_error(kwargs):
    error_handler('PARSE_ERROR', kwargs)


def translate_twitter_error(kwargs):
    error_handler('TRANSLATE_ERROR', kwargs)

def parse_error_decorator(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            parse_error(
                {'url': '',
                 'file_name': traceback.extract_tb(exc_traceback)[1].filename,
                 'line': traceback.extract_tb(exc_traceback)[1].lineno,
                 'vars': json.dumps({'args': args[1:], 'kwargs': kw}),
                 'error_message': exc_value.args[0]
                 }
            )
            raise
    return wrapper


@parse_error_decorator
def translate_request(content, target_lang='zh-CHS'):
    host = "https://openapi.youdao.com/api"
    appk, apps, salt = ('5479f92f6b8976fd', 'TK4X01ekWwWLZaUhOl0mbhKHT6EMDPqJ', 'mytk')
    params = {
        'from': 'auto',
        'to': target_lang,
        'q': content,
        'appKey': appk,
        'salt': salt,
        'sign': hashlib.md5('{}{}{}{}'.format(appk, content, salt, apps).encode(encoding='utf-8')).hexdigest()
    }

    url = '{host}?{param}'.format(host=host, param=parse.urlencode(params))
    r = requests.get(url, timeout=10)
    # todo 捕获异常
    if r.status_code == 200:
        if r.json()['errorCode'] == '0':
            return r.json()['translation'][0]
        else:
            translate_twitter_error({'url': url})
    return content
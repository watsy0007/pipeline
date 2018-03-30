import requests
import sys
import traceback
import json
import hashlib
from urllib import parse
from scrapy.utils.project import get_project_settings
from google.cloud import translate
import os


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
    kwargs['error_type'] = monitor_type
    print('data: {}'.format(kwargs))
    requests.post(get_project_settings().get('ERROR_COLLECTION_URL'), data=kwargs)


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
                 'error_message': str(exc_value.args[0])
                 }
            )
            raise

    return wrapper


def get_google_trans_path():
    # volume 映射
    return '/app/configs/mytoken-trans.json'


@parse_error_decorator
def get_translation(text, urls):
    if urls:
        for url in urls:
            text = text.replace(url['url'], '')
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = get_google_trans_path()
    trans_client = translate.Client(target_language='zh-CN')
    translated = trans_client.translate(text)['translatedText']
    return translated


@parse_error_decorator
def upload_assets(url_old):
    url = 'https://api.mytokenio.com/common/uploadimage?resourceUrls={remote}&debug=ico'.format(remote=url_old)
    r = requests.get(url)
    if r.status_code == 200 and int(r.json()['code']) == 0:
        return r.json()['data']['urls'][0]
    return url_old


@parse_error_decorator
def translate_request(text, target_lang='zh-CHS'):
    app_key = '5479f92f6b8976fd'
    app_secret = 'TK4X01ekWwWLZaUhOl0mbhKHT6EMDPqJ'
    salt = 'mytk'
    support_lang = ('zh-CHS', 'ja', 'EN', 'ko', 'fr', 'ru', 'pt', 'es')
    if target_lang not in support_lang:
        return None

    host = "https://openapi.youdao.com/api"
    params = {
        'from': 'auto',
        'to': target_lang,
        'q': text,
        'appKey': app_key,
        'salt': salt,
        'sign': hashlib.md5('{}{}{}{}'
                            .format(app_key, text, salt, app_secret)
                            .encode(encoding='utf-8')).hexdigest()
    }

    url = '{host}?{param}'.format(host=host, param=parse.urlencode(params))
    r = requests.get(url, timeout=12)
    if r.status_code == 200:
        if r.json()['errorCode'] == '0':
            return r.json()['translation'][0]
        else:
            print(r.json())
            # translate_twitter_error({'url': url, 'request': json.dumps(params), 'response': json.dumps(r.json())})
    return text


if __name__ == '__main__':
    print(get_translation(
        "Meet us tomorrow at @chatbotsummit TLV, where we'll talk about how Bancor uses #chatbots to let anyone set up a\u2026 <a href=\"https://twitter.com/i/web/status/958365458687807488\" target=\"_blank\">https://t.co/4jLMgYq9z9</a>"))

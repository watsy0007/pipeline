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


def translate_data():
    return {
        "type": "service_account",
        "project_id": "mytoken-trans",
        "private_key_id": "323783fd954a286d4f2279311291e5d670738e05",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCC3cxpyU/R92pC\nIFe6T/HSbJXNfiPT7PFtDU/wVngQhcI0GBlwAvZkI/fVioxplnseqEtzWLI9uD4F\n8G5cfwE3ZqERwLGpfrb+GZ7vs34EBHgQpy/FI/u0AsZkwUneLDS30K3UAGjaNdcw\ngPttw6oKQjC9MhuZrxSZwXS1aFJp+1mDep404lG/fOOUlxttgTN3m8QgjDYCqL70\n3Ljfo+05flnk5Ce7RGuItJzUnZsd2V/jYmYoj7vqD7nUHnJajLls8yh+hpcEj8hh\nXrqqeDACKmnmaorK3of5g/JpakXy3od5AwS/dBoav1OWUQV/E73h9Ua0rdqjrkWF\nUXLpDnrvAgMBAAECggEAATmdT8I0LpV/16Wg3Jwh+ePNVTKgmDvIGMq+nFPa5OCz\nrDQrjMpiTxatG8EjxltDxMozhp1mccB3SCvzhIcl1kRuLpHct+b5RJCt1bWa8OOv\n0gwWnORU118NR2Ut0VgdmDjqX6kvUhed75TNhb4GqfjrpuHAs2QZr8TJWGdlGhve\nUd4hgnqVyyC4lH6TZV/48TDL0eWAWqf+OqEBdpoNccAlxDcMOQGFIe8vJgp9D5yQ\n5KXtEmbcCthxwPF6AeGByfljEisXfGVLivXKiDWGXPYweE0cBx/NrS1Jtn+PAHof\ntPR4Krc5PbPV4UJfL0YEvK6CyjikKWVA0TbyGaFdKQKBgQC3TK9mdQUff+WNVLZH\nfmPi5hfmT+/drlWJHbgIypYzd6B9weUCaXSCgXqNeOmJtE1+lf2oLdJVzsrqHzBA\ns0iKsIRPZ8vYkeuo4Lpbuy2108fmlriH1q7ADgnD2U45eoaE4p49GVeSrw9FLzjQ\n4f6smK+eF3nJap1HeCSYJ3pIaQKBgQC2xVCW19FmHFM73wE2bqXXR/mI0YUU340N\nGtpfth3FhfLs4prRAc1ZS4c4yI5DBs6kf8A+J9Wf0F95y14LiCxTrEtcTLL1vg0Y\nF/l/sOJWF58L+UkjMgOh9KwXs6xtQ4Fz2HVrj9UxSJq9nrI0WCWLrHsVAmwIBwdO\nZBFkN679lwKBgCgkEwVM+yI6z/pzYrelZhp6aSF2wAC7/N9aMsM6GkqLGApyO8Sb\nc3hhAoWYxQvzAEWIc1QxNK616pn62oZQvMIihdcd0/ZJfmItVKJiC1CWYGCPATo+\nOWa1rE3HeOn9exf+yMh4lET7MUzlWnvkAfGqPktQuMrzHh5YoSrw+kaBAoGAHTUQ\n+NoKS4ARSQsNHY63D90fol6hHsHOv55f8VWgElWiiXp49ReNokxwkoFyQoHO+fi0\nVvp0p/Jbn5IBOGSNeN2auWhEXQL/Aq+qHl68/LcPopE2v9oZPINmEO+UiW11PXcE\n5Kh6kEKi/9Rhc/32Ggj5LlVRwEKnRz60jMhdPYcCgYBn1oEiAl+PwSjrU5NUMb2L\nQ4MN1ev1evPv81u7cfrAd/QJU5b9Ox2Wp3inShTWPq1ODUKGQzYfMZObyQaJnHsX\nNzN16tjTHTLUa6Mi4DSO7TPeyqESAVRoMA1PjDiIBQK+Hn6XIEwlKfn524YUiota\nDipbveY6fZnzHx5vTiu8rg==\n-----END PRIVATE KEY-----\n",
        "client_email": "mytoken@mytoken-trans.iam.gserviceaccount.com",
        "client_id": "112691825315781514545",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://accounts.google.com/o/oauth2/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mytoken%40mytoken-trans.iam.gserviceaccount.com"
    }


def get_google_trans_path():
    json_path = os.path.abspath(os.path.abspath(os.path.dirname(__file__)) + '/../mytoken-trans.json')
    if not os.path.exists(json_path):
        with open(json_path, 'a') as file:
            file.write(json.dumps(translate_data()))
    return json_path


@parse_error_decorator
def get_translation(text):
    trans_client = translate.Client(target_language='zh-CN')
    return trans_client.translate(text)['translatedText']


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


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = get_google_trans_path()


if __name__ == '__main__':
    print(get_translation("Meet us tomorrow at @chatbotsummit TLV, where we'll talk about how Bancor uses #chatbots to let anyone set up a\u2026 <a href=\"https://twitter.com/i/web/status/958365458687807488\" target=\"_blank\">https://t.co/4jLMgYq9z9</a>"))

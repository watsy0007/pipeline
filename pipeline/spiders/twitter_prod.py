# -*- coding: utf-8 -*-
import scrapy
import arrow
from scrapy import Request
import json
from urllib import parse
from pipeline.utils import api_error, get_translation
import requests
from scrapy_twitter import TwitterUserTimelineRequest, to_item
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from time import sleep

class TwitterProdSpider(scrapy.Spider):
    name = 'twitter_prod'
    allowed_domains = ["twitter.com", '35.176.110.161', 'lb-internalapi-1863620718.eu-west-2.elb.amazonaws.com']

    def __init__(self, *args, **kwargs):
        super(TwitterProdSpider, self).__init__(*args, **kwargs)
        self.host = kwargs.get('host')
        if self.host is None:
            self.host = 'lb-internalapi-1863620718.eu-west-2.elb.amazonaws.com'
        self.base_url = 'http://{}:12306/social/accountlist'.format(self.host)
        self.commit_url = 'http://{}:12306/social/addtimeline'.format(self.host)

        self.common_query = 'page_limit=50&need_pagination=1'
        # self.headers = {'Connection': 'close'}
        self.debug_screen = kwargs.get('debug_screen')
        self.debug_mode = kwargs.get('debug_mode')
        self.count = 50

    def start_requests(self):
        url = '{url}?page_num=1&{query}'.format(url=self.base_url,query=self.common_query)
        return [Request(url, callback=self.parse, errback=self.parse_error)]

    def yield_next_page_request(self, response, data):
        if len(data['data']['list']) == 0:
            self.logger.info('url {} response {}'.format(response.request.url,  data['data']))
            return None

        query = dict(map(lambda x: x.split('='), parse.urlparse(response.request.url)[4].split('&')))
        page = int(query['page_num'])
        url = '{url}?page_num={page}&{query}'.format(url=self.base_url,page=page + 1,query=self.common_query)
        self.logger.info(url)
        return Request(url, callback=self.parse, errback=self.parse_error)

    def parse_error(self, response):
        self.logger.error('error url {}, error{}'.format(response.request.url, repr(response)))
        api_error({'url': response.request.url})

    def parse(self, response):
        data = json.loads(response.body)
        if data['code'] != 0:
            api_error({'url': response.request.url, 'response': response.body})
            self.logger.error('{} error {}'.format(response.request.url, response.body))
            return
        for item in data['data']['list']:
            if self.debug_screen is not None:
                if self.debug_screen != item['account']:
                    continue
                self.logger.info('debug screen {} {}'.format(self.debug_screen, item))

            kwargs = {
                'screen_name': item['account'],
                'count': self.count,
                'callback': self.parse_twitter_time_line,
                'errback': self.parse_twitter_error,
                'meta':  {
                    'social_id': item['id'],
                    'last_content_id': item['last_social_content_id'],
                    'screen_name': item['account'],
                    'need_review': item['need_review']
                }
            }
            if str(item['last_social_content_id']) == '0':
                kwargs['since_id'] = item['last_social_content_id']
            yield TwitterUserTimelineRequest(**kwargs)
        next_page_generator = self.yield_next_page_request(response, data)
        if next_page_generator is not None:
            yield next_page_generator

    def parse_twitter_error(self, failure):
        self.logger.error('parse twitter error {}, meta {}'.format(repr(failure), failure.request.meta))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def parse_twitter_time_line(self, response):
        account_id = response.request.meta['social_id']
        need_review = response.request.meta['need_review']
        last_content_id = response.request.meta['last_content_id']
        account = response.request.meta['screen_name']
        self.logger.info('twitter: {}, last_id: {}, count: {}'.format(account, last_content_id, len(response.tweets)))
        for tweet in response.tweets:
            item = self.format_request(to_item(tweet))
            if item['retweet_content'] is not None:
                item['retweet_content'] = json.dumps(item['retweet_content'])
            item['social_account_id'] = account_id
            if need_review:
                item['review_status'] = 0
            else:
                item['review_status'] = 1
            r = requests.post(url=self.commit_url, data={k: str(item[k]) for k in item}, timeout=6)
            # self.logger.info('post to prod %s', json.dumps({k: str(item[k]) for k in item}))
            # self.logger.error('{} => {} {}'.format(self.commit_url, r.status_code, r.json()))
            if r.status_code == 200:
                # todo 判断code是否成功,否则捕获api错误
                result = r.json()
                if int(result['code']) != 0:
                    api_error({'url': response.request.url,
                               'response': json.dumps(r.json()),
                               'vars': json.dumps({k: str(item[k]) for k in item})})
            else:
                # todo 捕获异常
                self.logger.error('{} - {}'.format(r.status_code, r.content))

    ##############################################################
    # data format
    ##############################################################

    def format_request(self, data):
        item = self.default_time_line_struct(data)
        return self.extend_retweet_struct(item, data)

    def default_time_line_struct(self, data):
        translation = None
        if self.debug_mode is None:
            translation = self.format_tweet_urls(get_translation(data['full_text']), data['urls'])
        return {
            'social_content_id': data['id'],
            'posted_at': arrow.get(data['created_at'], 'ddd MMM DD HH:mm:ss ZZ YYYY').timestamp,
            'content': self.format_tweet_urls(data['full_text'], data['urls']),
            'content_translation': translation,
            'i18n_content_translation': json.dumps({'zh_cn': translation}),
            'is_reweet': 0,
            'retweet_content': {}
        }

    @classmethod
    def format_tweet_urls(cls, content, urls):
        f_url = lambda x: '<a href="{}" target="_blank">{}</a>'.format(x['expanded_url'], x['url'])
        for url in urls:
            content = content.replace(url['url'], f_url(url))
        return content

    def extend_retweet_struct(self, item, data):
        if 'retweeted_status' not in data.keys():
            return item
        status = data['retweeted_status']
        retweet = item['retweet_content']
        retweet['account'] = status['user']['screen_name']
        retweet['nickname'] = status['user']['name']
        retweet['content'] = self.format_tweet_urls(status['full_text'], data['urls'])
        if self.debug_mode is None:
            retweet['content_translation'] = json.dumps(
                {
                    'zh_cn': self.format_tweet_urls(get_translation(status['full_text']),data['urls'])
                })
        item['is_reweet'] = 1
        return item

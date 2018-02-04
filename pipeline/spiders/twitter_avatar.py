# -*- coding: utf-8 -*-
import scrapy
import arrow
from scrapy import Request
import json
from urllib import parse
from pipeline.utils import spider_error, api_error, translate_request
import requests
from scrapy_twitter import TwitterUserTimelineRequest, to_item
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class TwitterSpider(scrapy.Spider):
    name = 'twitter_avatar'
    allowed_domains = ["twitter.com", '127.0.0.1', '35.176.110.161']

    def __init__(self, *args, **kwargs):
        super(TwitterSpider, self).__init__(*args, **kwargs)
        self.base_url = 'http://35.176.110.161:12306/social/accountlist'
        self.commit_url = 'http://35.176.110.161:12306/social/addtimeline'
        self.common_query = 'page_limit=40&need_pagination=1'
        # self.headers = {'Connection': 'close'}
        self.count = 50

    def start_requests(self):
        url = '{url}?page_num=1&{query}'.format(url=self.base_url,query=self.common_query)
        return [Request(url, callback=self.parse, errback=self.parse_error)]

    def yield_next_page_request(self, response, data):
        if len(data['data']['list']) == 0:
            return None

        query = dict(map(lambda x: x.split('='), parse.urlparse(response.request.url)[4].split('&')))
        page = int(query['page_num'])
        url = '{url}?page_num={page}&{query}'.format(url=self.base_url,page=page + 1,query=self.common_query)
        return Request(url, callback=self.parse, errback=self.parse_error)

    def parse_error(self, response):
        api_error({'url': response.request.url})

    def parse(self, response):
        data = json.loads(response.body)
        if data['code'] != 0:
            api_error({'url': response.request.url, 'response': response.body})
            self.logger.error('{} error {}'.format(response.request.url, response.body))
            return
        for item in data['data']['list']:
            yield TwitterUserTimelineRequest(
                screen_name=item['account'],
                count=self.count,
                since_id=item['last_social_content_id'],
                callback=self.parse_twitter_time_line,
                errback=self.parse_twitter_error,
                meta={'social_id': item['id'],
                      'last_content_id': item['last_social_content_id'],
                      'screen_name': item['account']})

        next_page_generator = self.yield_next_page_request(response, data)
        if next_page_generator is not None:
            yield next_page_generator

    def parse_twitter_error(self, failure):
        # log all failures
        self.logger.error('parse twitter error {}'.format(repr(failure)))

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def parse_twitter_time_line(self, response):
        account_id = response.request.meta['social_id']
        last_content_id = response.request.meta['last_content_id']
        account = response.request.meta['screen_name']
        self.logger.info('twitter: {}, last_id: {}, count: {}'.format(account, last_content_id, len(response.tweets)))
        for tweet in response.tweets:
            item = self.format_request(to_item(tweet))
            if item['retweet_content'] is not None:
                item['retweet_content'] = json.dumps(item['retweet_content'])
            item['social_account_id'] = account_id
            self.logger.info('post to prod %s', json.dumps({k: str(item[k]) for k in item}))
            r = requests.post(url=self.commit_url, data={k: str(item[k]) for k in item}, timeout=5)
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

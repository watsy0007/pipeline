# -*- coding: utf-8 -*-
import scrapy
import arrow
from scrapy import Request
import json
from urllib import parse
from pipeline.utils import spider_error, api_error, translate_request
import requests
from pipeline.utils import upload_assets
from scrapy_twitter import TwitterUserShowRequest, to_item
from pipeline.items import TwitterAvatarItem
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


class TwitterAvatarSpider(scrapy.Spider):
    name = 'twitter_avatar'
    allowed_domains = ["twitter.com", '127.0.0.1', '35.176.110.161',
                       'lb-internalapi-1863620718.eu-west-2.elb.amazonaws.com']

    def __init__(self, *args, **kwargs):
        super(TwitterAvatarSpider, self).__init__(*args, **kwargs)
        self.host = kwargs.get('host')
        if self.host is None:
            self.host = 'lb-internalapi-1863620718.eu-west-2.elb.amazonaws.com'
        self.base_url = 'http://{}:12306/social/accountlist'.format(self.host)
        self.commit_url = 'http://{}:12306/social/addtimeline'.format(self.host)
        self.update_url = 'http://{}:12306/social/updateaccount'.format(self.host)

        self.common_query = 'page_limit=50&need_pagination=1'
        # self.headers = {'Connection': 'close'}
        self.debug_screen = kwargs.get('debug_screen')
        self.debug_mode = kwargs.get('debug_mode')
        self.count = 50

    def start_requests(self):
        url = '{url}?page_num=1&{query}'.format(url=self.base_url, query=self.common_query)
        return [Request(url, callback=self.parse, errback=self.parse_error)]

    def yield_next_page_request(self, response, data):
        if len(data['data']['list']) == 0:
            return None

        query = dict(map(lambda x: x.split('='), parse.urlparse(response.request.url)[4].split('&')))
        page = int(query['page_num'])
        url = '{url}?page_num={page}&{query}'.format(url=self.base_url, page=page + 1, query=self.common_query)
        self.logger.info(url)
        return Request(url, callback=self.parse, errback=self.parse_error)

    def parse_error(self, response):
        # self.logger.error('error url {}, error{}'.format(response.request.url, repr(response)))
        api_error({'url': response.request.url})

    def parse(self, response):
        data = json.loads(response.body)
        if data['code'] != 0:
            # api_error({'url': response.request.url, 'response': response.body})
            self.logger.error('{} error {}'.format(response.request.url, response.body))
            return
        for item in data['data']['list']:
            if self.debug_screen is not None:
                if self.debug_screen != item['account']:
                    continue
                self.logger.info('debug screen {} {}'.format(self.debug_screen, item))

            yield TwitterUserShowRequest(
                screen_name=item['account'],
                callback=self.parse_twitter_user_show,
                errback=self.parse_twitter_error,
                meta={'social_id': item['id'],
                      'source_avatar': item['source_avatar'],
                      'nickname': item['nickname']})

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

    def parse_twitter_user_show(self, response):
        account_id = response.request.meta['social_id']
        source_avatar = response.request.meta['source_avatar']
        nickname_old = response.request.meta['nickname']

        nickname = response.user['name']
        image_url = response.user['profile_image_url']
        image_url = image_url if image_url is None else image_url.replace('_normal', '')

        if source_avatar == image_url and nickname == nickname_old:
            return

        item = TwitterAvatarItem()
        item['social_account_id'] = account_id
        if source_avatar != image_url:
            item['source_avatar'] = image_url
            item['avatar'] = upload_assets(image_url)
        if nickname != nickname_old:
            item['nickname'] = nickname
        yield item

    ##############################################################
    # data format
    ##############################################################

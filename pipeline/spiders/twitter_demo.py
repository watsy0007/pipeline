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
import re

class TwitterDemoSpider(scrapy.Spider):
    name = 'twitter_demo'
    allowed_domains = ["twitter.com", '127.0.0.1', '52.56.166.200']

    def __init__(self, *args, **kwargs):
        super(TwitterDemoSpider, self).__init__(*args, **kwargs)
        self.base_url = 'http://52.56.166.200:12306/social/accountlist'
        self.commit_url = 'http://52.56.166.200:12306/social/addtimeline'
        self.common_query = 'page_limit=40&need_pagination=1'
        self.screen_name = kwargs.get('screen_name')
        self.since_id = kwargs.get('since_id')
        if self.since_id is None:
            self.since_id = 0
        self.social_id = kwargs.get('social_id')
        # self.headers = {'Connection': 'close'}
        self.count = 50

    def start_requests(self):
        url = '{url}?page_num=1&{query}'.format(url=self.base_url,query=self.common_query)
        return [Request(url, callback=self.parse, errback=self.parse_error)]

    def parse_error(self, response):
        api_error({'url': response.request.url})

    def parse(self, response):
        data = json.loads(response.body)

        yield TwitterUserTimelineRequest(
            screen_name=self.screen_name,
            count=self.count,
            since_id=self.since_id,
            callback=self.parse_twitter_time_line,
            errback=self.parse_twitter_error,
            meta={'social_id': self.social_id,
                  'last_content_id': self.screen_name,
                  'screen_name': 'hitbtc',
                  'need_review': 0})

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
        need_review = response.request.meta['need_review']
        account = response.request.meta['screen_name']
        self.logger.info('twitter: {}, last_id: {}, count: {}'.format(account, last_content_id, len(response.tweets)))
        for tweet in response.tweets:
            self.logger.info('response data : {}'.format(to_item(tweet)))
            item = self.format_request(to_item(tweet))
            self.logger.info('twitter {}'.format(to_item(tweet)))
            if item['retweet_content'] is not None:
                item['retweet_content'] = json.dumps(item['retweet_content'])
            item['social_account_id'] = account_id
            if need_review:
                item['review_status'] = 0
            else:
                item['review_status'] = 1
            self.logger.info('post to prod %s', json.dumps({k: str(item[k]) for k in item}))

    ##############################################################
    # data format
    ##############################################################

    def format_request(self, data):
        item = self.default_time_line_struct(data)
        return self.extend_retweet_struct(item, data)

    def default_time_line_struct(self, data):
        content, urls = self.get_content(data)
        transaction = self.format_tweet_urls(get_translation(content), urls)
        return {
            'social_content_id': data['id'],
            'posted_at': arrow.get(data['created_at'], 'ddd MMM DD HH:mm:ss ZZ YYYY').timestamp,
            'content': content,
            'content_translation': transaction,
            'i18n_content_translation': json.dumps({'zh_cn': transaction}),
            'is_reweet': 0,
            'retweet_content': {}
        }

    def get_content(self, data):
        if 'retweeted_status' not in data.keys():
            content = data['full_text']
            urls = data['urls']
        else:
            status = data['retweeted_status']
            tweet_prefix = ''
            try:
                tweet_prefix = re.search('RT @\w+:', data['full_text']).group(0)
            except Exception as e:
                self.logger.error('cant find prefix: {}'.format(e))
            content = '{}{}'.format(tweet_prefix, status['full_text'])
            urls = status['urls']
        return self.format_tweet_urls(content, urls), urls

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
        retweet['content'] = status['full_text']
        retweet['content_translation'] = \
            json.dumps({'zh_cn': self.format_tweet_urls(get_translation(status['full_text']),data['urls']) })
        item['is_reweet'] = 1
        return item

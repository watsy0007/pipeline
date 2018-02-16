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

class TwitterDemoSpider(scrapy.Spider):
    name = 'twitter_demo'
    allowed_domains = ["twitter.com", '127.0.0.1', '52.56.166.200']

    def __init__(self, *args, **kwargs):
        super(TwitterDemoSpider, self).__init__(*args, **kwargs)
        self.base_url = 'http://52.56.166.200:12306/social/accountlist'
        self.commit_url = 'http://52.56.166.200:12306/social/addtimeline'
        self.common_query = 'page_limit=40&need_pagination=1'
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
            screen_name='hitbtc',
            count=self.count,
            since_id=963402035155623936,
            callback=self.parse_twitter_time_line,
            errback=self.parse_twitter_error,
            meta={'social_id': 205,
                  'last_content_id': 963402035155623936,
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
            # r = requests.post(url=self.commit_url, data={k: str(item[k]) for k in item}, timeout=5)
            # if r.status_code == 200:
            #     # todo 判断code是否成功,否则捕获api错误
            #     result = r.json()
            #     self.logger.info('result:{}'.format(result))
            #     if int(result['code']) != 0:
            #         api_error({'url': response.request.url,
            #                    'response': json.dumps(r.json()),
            #                    'vars': json.dumps({k: str(item[k]) for k in item})})
            # else:
            #     # todo 捕获异常
            #     self.logger.error('{} - {}'.format(r.status_code, r.content))

    ##############################################################
    # data format
    ##############################################################

    def format_request(self, data):
        item = self.default_time_line_struct(data)
        return self.extend_retweet_struct(item, data)

    def default_time_line_struct(self, data):
        transaction = self.format_tweet_urls(get_translation(data['text']), data['urls'])
        return {
            'social_content_id': data['id'],
            'posted_at': arrow.get(data['created_at'], 'ddd MMM DD HH:mm:ss ZZ YYYY').timestamp,
            'content': self.format_tweet_urls(data['text'], data['urls']),
            'content_translation': transaction,
            'i18n_content_translation': json.dumps({'zh_cn': transaction}),
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
        retweet['content'] = status['text']
        retweet['content_translation'] = \
            json.dumps({'zh_cn': self.format_tweet_urls(get_translation(status['text']),data['urls']) })
        item['is_reweet'] = 1
        return item

# -*- coding: utf-8 -*-
import scrapy
import arrow
from scrapy import Request
import json
from urllib import parse
from pipeline.utils import spider_error, api_error, translate_request
import requests
from scrapy_twitter import TwitterUserTimelineRequest, to_item

class TwitterSpider(scrapy.Spider):
    name = 'twitter'
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
            print('{} error {}'.format(response.request.url, response.body))
            return

        for item in data['data']['list']:
            yield TwitterUserTimelineRequest(
                screen_name=item['account'],
                count=self.count,
                since_id=item['last_social_content_id'],
                callback=self.parse_twitter_time_line,
                meta={'social_id': item['id']})

        next_page_generator = self.yield_next_page_request(response, data)
        if next_page_generator is not None:
            yield next_page_generator

    def parse_twitter_time_line(self, response):
        # todo parse monitor
        account_id = response.request.meta['social_id']
        for tweet in response.tweets:
            item = self.format_request(to_item(tweet))
            if item['retweet_content'] is not None:
                item['retweet_content'] = json.dumps(item['retweet_content'])
            item['social_account_id'] = account_id
            # self.logger.info('post to prod %s', json.dumps({k: str(item[k]) for k in item}))
            r = requests.post(url=self.commit_url, data={k: str(item[k]) for k in item}, timeout=5)
            if r.status_code == 200:
                # todo 判断code是否成功,否则捕获api错误
                result = r.json()
                if int(result['code']) != 0:
                    api_error({'url': response.request.url,
                               'response': json.dumps(r.json())})
            else:
                # todo 捕获异常
                print('{} - {}'.format(r.status_code, r.content))

    ##############################################################
    # data format
    ##############################################################

    def format_request(self, data):
        item = self.default_time_line_struct(data)
        return self.extend_retweet_struct(item, data)

    def default_time_line_struct(self, data):
        return {
            'social_content_id': data['id'],
            'posted_at': arrow.get(data['created_at'], 'ddd MMM DD HH:mm:ss ZZ YYYY').timestamp,
            'content': self.format_tweet_urls(data['text'], data['urls']),
            'i18n_content_translation':
                json.dumps(
                    {'zh_cn': self.format_tweet_urls(translate_request(data['text']), data['urls'])}
                ),
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
            json.dumps({'zh_cn': self.format_tweet_urls(translate_request(status['text']),data['urls']) })
        item['is_reweet'] = 1
        return item

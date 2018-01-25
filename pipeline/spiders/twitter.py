# -*- coding: utf-8 -*-
import scrapy
import json
import arrow
from scrapy import FormRequest
from scrapy_twitter import TwitterUserTimelineRequest, to_item

class TwitterSpider(scrapy.Spider):
    name = "twitter"
    allowed_domains = ["twitter.com", '127.0.0.1']

    def __init__(self, screen_name = None, *args, **kwargs):
        if not screen_name:
            raise scrapy.exceptions.CloseSpider('Argument scren_name not set.')
        super(TwitterSpider, self).__init__(*args, **kwargs)
        self.count = 100

    start_urls = ['http://127.0.0.1:4567/twitters']

    def parse(self, response):
        data = json.loads(response.body)
        for item in data:
            yield TwitterUserTimelineRequest(
                screen_name=item['screen_name'],
                count=self.count,
                callback=self.parse_twitters,
                meta={'screen_name': item['screen_name']}
            )

    def parse_twitters(self, response):
        tweets = response.tweets
        for tweet in tweets:
            item = self.format_request(to_item(tweet))
            hash = {}
            for k in item.keys():
                hash[k] = str(item[k])
            yield FormRequest(url='http://127.0.0.1:4567/twitter',method='POST', formdata=hash, callback=self.upload_to_internal_api)
        return None

    def format_request(self, data):
        item = self.default_twitter_struct(data)
        item = self.retweet_struct(item, data)
        return item

    def upload_to_internal_api(self, response):
        print(response.status)
        return None


    ##############################################################
    # data format
    ##############################################################


    def replace_text_content(self, content, urls):
        for url in urls:
            content = content.replace(url['url'], '<a href="{}" target="_blank">{}</a>'.format(url['expanded_url'], url['url']))
        return content

    def media_struct(self, data):
        if 'media' in data.keys():
            return [{
                'media_type': media['type'],
                'http_url': media['media_url'],
                'https_url': media['media_url_https']
            } for media in data['media']]
        return []

    def default_twitter_struct(self, data):
        return {
            'msg_type': 'direct',
            'id': data['id'],
            'created_at': arrow.get(data['created_at'], 'ddd MMM DD HH:mm:ss ZZ YYYY').timestamp,
            'author': data['user']['name'],
            'account': data['user']['screen_name'],
            'text': data['text'],
            'html_text': self.replace_text_content(data['text'], data['urls']),
            # 'media': self.media_struct(data),
            'retweet_author': '',
            'retweet_account': '',
        }

    def retweet_struct(self, item, data):
        if 'retweeted_status' in data.keys():
            item['msg_type'] = 'retweet'
            retweet_item = data['retweeted_status']
            item['retweet_author'] = retweet_item['user']['name']
            item['retweet_account'] = retweet_item['user']['screen_name']
            item['retweet_text'] = retweet_item['text']
            # item['rwtweet_media'] = self.media_struct(data)
            item['retweet_html_text'] = self.replace_text_content(retweet_item['text'], retweet_item['urls'])
        return item
# -*- coding: utf-8 -*-
import scrapy
import json
from pipeline.items import CMCItem

class CoinmarketcapSpider(scrapy.Spider):
    name = 'cmc_detail'
    allowed_domains = ["coinmarketcap.com"]

    start_urls = ['https://api.coinmarketcap.com/v1/ticker/?convert=CNY&limit=3000']

    def parse(self, response):
        data = json.loads(response.body)
        for cmc in data:
            item = CMCItem()
            item['cmc_id'] = cmc['id']
            item['name'] = cmc['name']
            item['symbol'] = cmc['symbol']
            if cmc['total_supply'] is not None:
                item['total_supply'] = cmc['total_supply']
            else:
                item['total_supply'] = 0
            if cmc['max_supply'] is not None:
                item['max_supply'] = cmc['max_supply']
            else:
                item['max_supply'] = 0
            yield item


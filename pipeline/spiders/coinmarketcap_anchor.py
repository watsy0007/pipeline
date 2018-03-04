# -*- coding: utf-8 -*-
import scrapy
import json
import arrow
from scrapy.spiders.crawl import CrawlSpider
from scrapy import Request
from scrapy import Selector
from pipeline.items import CMCHistoryPriceItem
from datetime import datetime, timedelta

class CmcHistoryAnchorSpider(CrawlSpider):
    name = 'cmc_history_anchor'
    allowed_domains = ["coinmarketcap.com"]

    def __init__(self, *args, **kwargs):
        super(CmcHistoryAnchorSpider, self).__init__(*args, **kwargs)
        self.start_date = kwargs.get('start_date')
        if self.start_date is None:
            date_N_days_ago = datetime.now() - timedelta(days=3)
            self.start_date = arrow.Arrow.fromdate(date_N_days_ago).format('YYYYMMDD')
        self.end_date = arrow.now().format('YYYYMMDD')
        self.base_url = 'https://coinmarketcap.com/currencies'

    def start_requests(self):
        f_url = lambda x: '{}/{}/historical-data/?start={}&end={}'.format(
            self.base_url,
            x,
            self.start_date,
            self.end_date)
        urls = [f_url(symbol) for symbol in ('bitcoin', 'ethereum', 'tether')]

        print(urls)
        return [Request(url=url, callback=self.parse) for url in urls]

    def parse(self, response):
        hxs = Selector(response=response)
        symbol = hxs.xpath("//*[@class='text-large']/small/text()").extract_first()
        symbol = symbol.replace('(', '').replace(')', '').lower()
        for item in hxs.xpath("//*[@class='table-responsive']/table/tbody/tr"):
            data = [i.extract() for i in item.xpath("./td/text()")]
            history = CMCHistoryPriceItem()
            history['date'] = arrow.get(data[0], 'MMM DD, YYYY').timestamp
            history['rate'] = data[1]
            history['symbol'] = symbol
            history['anchor'] = 'usd'
            yield history



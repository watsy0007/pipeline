from scrapy import Request
from scrapy.spiders.crawl import CrawlSpider
from scrapy.selector.lxmlsel import HtmlXPathSelector

from pipeline.items import IcoItem


class CoingeckoSpider(CrawlSpider):
    name = 'coingecko'
    start_urls = ["https://www.coingecko.com/en"]
    allowed_domains = ["coingecko.com"]
    item_counts = 0

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        for data in hxs.xpath("//*[@id='gecko-table']/tbody/tr"):
            item = IcoItem()
            item["name"] = data.xpath(
                './/td[@class="coin-name"]//span[@class="coin-content-name"]/text()').extract_first()
            item["symbol"] = data.xpath(
                './/td[@class="coin-name"]//span[@class="coin-content-symbol"]/text()').extract_first()
            item["img_url"] = "https:" + data.xpath('.//td[@class="coin-name"]//img/@data-src').extract_first()
            item["other"] = data.xpath('.//td[@class="coin-name"]//small/text()').extract_first()
            item["developer"] = data.xpath('.//td[@class="td-developer_score dev"]/div[1]/text()').extract_first()
            item["community"] = data.xpath('.//td[@class="td-community_score community"]/div[1]/text()').extract_first()
            item["public_interest"] = data.xpath(
                './/td[@class="td-public_interest_score pb-interest"]/div[1]/text()').extract_first()
            item["total"] = data.xpath('.//td[@class="total"]/div[1]/text()').extract_first()
            coin_name = data.xpath('.//td[@class="coin-name"]//a[@class="currency_exchangable_chart_link"]/@href').re(
                r'price_charts/([\S\s]+?)/usd')
            url = "https://www.coingecko.com/en/coins/{}#panel".format(coin_name[0])
            yield Request(url=url, callback=self.parse_baseinfo, meta={"item": item, "coin_name": coin_name[0]},
                          dont_filter=True)
        next_page_url = hxs.xpath('//link[@rel="next"]/@href').extract_first()
        self.logger.info("current page url <{}>".format(next_page_url))
        yield response.follow(next_page_url, self.parse)

    def parse_baseinfo(self, response):
        item = response.meta.get("item")
        coin_name = response.meta.get("coin_name")
        hxs = HtmlXPathSelector(response)
        item['liquidity'] = hxs.xpath(
            '//div[@class="score"][contains(text(), "Liquidity")]/span/text()').extract_first()
        item["hash_algorithm"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Hashing Algorithm")]/following-sibling::p[1]/text()').extract_first()
        item["hash_rate"] = hxs.xpath('//div[@class="hashrate"]/p/text()').extract_first()
        item["block_time"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Block Time")]/following-sibling::p[1]/text()').extract_first()
        item["homepage"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Homepage")]/following-sibling::p[1]/a/text()').extract_first()
        item["block_chain_supply"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Blockchain/Supply")]/following-sibling::p[1]/a/text()').extract_first()
        item["discussion_forum"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Discussion Forum")]/following-sibling::p[1]/a/text()').extract_first()
        item["available_total_supply"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Available/Total Supply")]/following-sibling::p[1]/text()').extract_first()
        url = "https://www.coingecko.com/en/coins/{}/social#panel".format(coin_name)
        yield Request(url=url, callback=self.parse_community, meta={"item": item, "coin_name": coin_name},
                      dont_filter=True)

    def parse_community(self, response):
        item = response.meta.get("item")
        coin_name = response.meta.get("coin_name")
        hxs = HtmlXPathSelector(response)
        item['subscribers'] = hxs.xpath(
            '//a[@rel="nofollow"][contains(text(),"Subscribers")]/../following-sibling::p[1]/text()').extract_first()
        item["followers"] = hxs.xpath(
            '//a[@rel="nofollow"][contains(text(),"Followers")]/../following-sibling::p[1]/text()').extract_first()
        item["likes"] = hxs.xpath(
            '//a[@rel="nofollow"][contains(text(),"Likes")]/../following-sibling::p[1]/text()').extract_first()
        item["avg_users_online"] = hxs.xpath(
            '//div[contains(@class, "social-media")][contains(text(), "Online")]/p[1]/text()').extract_first()
        item["avg_new_hot_posts_per_hour"] = hxs.xpath(
            '//div[contains(@class, "social-media")][contains(text(), "New Hot")]/p[1]/text()').extract_first()
        item["avg_new_comments_on_hot_posts_per_hour"] = hxs.xpath(
            '//div[contains(@class, "col-md")][contains(text(), "Comments")]/p[1]/text()').extract_first()
        url = "https://www.coingecko.com/en/coins/{}/developer#panel".format(coin_name)
        yield Request(url=url, callback=self.parse_developer, meta={"item": item}, dont_filter=True)

    def parse_developer(self, response):
        item = response.meta.get("item")
        hxs = HtmlXPathSelector(response)
        item["stars"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Stars")]/following-sibling::p[1]/text()').extract_first()
        item["watchers"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Watchers")]/following-sibling::p[1]/text()').extract_first()
        item["forks"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Forks")]/following-sibling::p[1]/text()').extract_first()
        item["merged_pull_requests"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Merged Pull Requests")]/following-sibling::p[1]/text()').extract_first()
        item["total_issues"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Total Issues")]/following-sibling::p[1]/text()').extract_first()
        item["closed_issues"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Closed Issues")]/following-sibling::p[1]/text()').extract_first()
        item["contributors"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Contributors")]/following-sibling::p[1]/text()').extract_first()
        item["total_new_commits"] = hxs.xpath(
            '//div[@class="tab-title"][contains(text(), "Total new commits")]/following-sibling::p[1]/text()').extract_first()
        yield item
        self.item_counts += 1
        self.logger.info("current item counts <{}>".format(self.item_counts))

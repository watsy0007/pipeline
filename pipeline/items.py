# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class PipelineItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class IcoItem(Item):
    coin_name = Field()
    coin_symbol = Field()
    coin_img_url = Field()
    coin_other = Field()
    developer = Field()
    community = Field()
    public_interest = Field()
    total = Field()

    # overview
    liquidity = Field()
    hashing_algorithm = Field()
    hashrate = Field()
    block_time = Field()
    homepage = Field()
    blockchain_supply = Field()
    discussion_forum = Field()
    available_total_supply = Field()

    # community
    ubscribers = Field()
    followers = Field()
    likes = Field()
    average_users_online = Field()
    average_new_hot_posts_per_hour = Field()
    average_new_comments_on_hot_posts_per_hour = Field()

    #developer
    stars = Field()
    watchers = Field()
    forks = Field()
    merged_pull_requests = Field()
    total_issues = Field()
    closed_issues = Field()
    contributors = Field()
    total_new_commits = Field()
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import requests
from scrapy.utils.project import get_project_settings

repr_str = ['\r', '\n', '\t']
def item_etls(string=None):
    if not string:
        return string
    for x in repr_str:
        string.replace(x, "")
    return string.strip()

class PipelinePipeline(object):
    def process_item(self, item, spider):
        return item

class IcoPipeline(object):
    def process_item(self, item, spider):
        for k in item.keys():
            item[k] = item_etls(item[k])

        # todo save data
        # interface_url = ""
        r = requests.post(url=get_project_settings().get('GECKOSES_URL'), data=dict(item))
        # print('status {}'.format(r.status_code))
        return item
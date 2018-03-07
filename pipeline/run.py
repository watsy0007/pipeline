from scrapy import cmdline


cmd = 'scrapy crawl twitter_avatar -a debug_screen=mytokenio'
cmdline.execute(cmd.split())
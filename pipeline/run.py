from scrapy import cmdline

name = 'twitter'
cmd = 'scrapy crawl {0} -a screen_name=watsy0007 -o zb_tweets.json'.format(name)
cmdline.execute(cmd.split())
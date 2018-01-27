from scrapy import cmdline

name = 'twitter'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())
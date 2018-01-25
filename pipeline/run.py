from scrapy import cmdline

name = 'twitter'
cmd = 'scrapy crawl {0} -a screen_name=watsy0007'.format(name)
cmdline.execute(cmd.split())
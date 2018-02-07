from scrapy import cmdline

name = 'cmc_history_anchor'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())
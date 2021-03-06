# -*- coding: utf-8 -*-

# Scrapy settings for pipeline project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'pipeline'

SPIDER_MODULES = ['pipeline.spiders']
NEWSPIDER_MODULE = 'pipeline.spiders'

DOWNLOADER_MIDDLEWARES = {
    'scrapy_twitter.TwitterDownloaderMiddleware': 101,
}
TWITTER_CONSUMER_KEY        = '7ItrbuzK8X943zg1LUS3F3P44'
TWITTER_CONSUMER_SECRET     = 'xgwCM99SS8mscxoWOYdyFL1E1ao5IkxkjyvvL2Mo68k6nxmXdS'
TWITTER_ACCESS_TOKEN_KEY    = '907153297143820289-fsGn38Kwrju9LQnhdvURXsFtYi20s32'
TWITTER_ACCESS_TOKEN_SECRET = '9NE2Db7z0v1q7oKp4l4vcH5XMpgn9o19VW9bXLkVg8ALQ'
TWITTER_TEXT_MODE           = 'extended'
# PROXIES = {'http': 'http://127.0.0.1:1087'}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'pipeline (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

ERROR_COLLECTION_URL = 'http://host:4000/api/v1/handle_errors'
GECKOSES_URL = 'http://host:4000/api/v1/geckoses'
CMC_URL = 'http://host:4000/api/v1/cmc'
CMC_HISTORY_URL = 'http://172.31.24.214:12306/currencyratehistory/create'
LOG_LEVEL = 'INFO'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 24

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# DEFAULT_REQUEST_HEADERS = {
#     'Connection': 'close'
# }

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'pipeline.middlewares.PipelineSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'pipeline.middlewares.PipelineDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'pipeline.pipelines.IcoPipeline': 300,
    'pipeline.pipelines.CmcPipeline': 400,
    'pipeline.pipelines.CMCHistoryPricePipeline': 401,
    'pipeline.pipelines.TwitterAvatarPipeline': 402,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

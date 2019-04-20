from scrapy import cmdline

name = 'getproxy'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())

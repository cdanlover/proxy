# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ProxyItem(scrapy.Item):
	# define the fields for your item here like:
	# name = scrapy.Field()
	proxyip = scrapy.Field()
	proxyport = scrapy.Field()
	address = scrapy.Field()
	source = scrapy.Field()
	type = scrapy.Field()

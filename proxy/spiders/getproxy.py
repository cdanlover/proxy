# -*- coding: utf-8 -*-
import scrapy

from proxy.items import ProxyItem


class GetproxySpider(scrapy.Spider):
	name = 'getproxy'
	allowed_domains = ['www.xicidaili.com',
	                   'www.kuaidaili.com',
	                   'www.66ip.cn',
	                   'www.ip3366.net',
	                   'www.swei360.com'
	                   ]
	start_urls = ['http://www.xicidaili.com/nn/',
	              'https://www.kuaidaili.com/ops/proxylist/',
	              'http://www.66ip.cn/areaindex_1/1.html',
	              'http://www.66ip.cn/1.html',
	              'http://www.ip3366.net/?stype=1&page=1',
	              'http://www.swei360.com/free/?page=1'
	              ]
	
	def start_requests(self):
		# 360代理只有前7页的信息
		for page in range(1, 8):
			url = 'http://www.swei360.com/free/?page='
			url = url + str(page)
			yield scrapy.Request(url, callback=self.swei360_parse)
		
		# xicidaili只要获取前50页的信息
		for page in range(1, 51):
			url = 'http://www.xicidaili.com/nn/'
			url = url + str(page)
			yield scrapy.Request(url, callback=self.xici_parse)
		
		# 66ip地区性只要获取前34页的信息
		for page in range(1, 35):
			url = 'http://www.66ip.cn/areaindex_'
			url = url + str(page) + '/1.html'
			yield scrapy.Request(url, callback=self.sixip_area_parse)
		
		# 66ip全国代理只要获取前50页的信息
		for page in range(1, 51):
			url = 'http://www.66ip.cn/'
			url = url + str(page) + '.html'
			yield scrapy.Request(url, callback=self.sixip_parse)
		
		# 云代理ip3366.net只有前10页的信息
		for page in range(1, 11):
			url = 'http://www.ip3366.net/?stype=1&page='
			url = url + str(page)
			yield scrapy.Request(url, callback=self.yun_parse)
		
		# kuaidaili只要获取前10页的信息
		for page in range(1, 11):
			url = 'https://www.kuaidaili.com/ops/proxylist/'
			url = url + str(page)
			yield scrapy.Request(url, callback=self.kuaidaili_parse)
	
	# 西刺免费代理IP
	def xici_parse(self, response):
		# 获取代理的信息
		proxys = response.xpath('//tr[@class="odd" or @class=""]')
		for each_proxy in proxys:
			item = ProxyItem()
			try:
				item['proxyip'] = each_proxy.xpath('./td[2]/text()').extract()[0]
				item['proxyport'] = each_proxy.xpath('./td[3]/text()').extract()[0]
				item['address'] = each_proxy.xpath('./td[4]/a/text()').extract()[0]
				item['type'] = each_proxy.xpath('./td[6]/text()').extract()[0]
				item['source'] = 'xicidaili'
			except Exception:
				pass
			yield item
	
	# 快代理
	def kuaidaili_parse(self, response):
		# 获取代理的信息
		proxys = response.xpath('//div[@id="freelist"]/table/tbody/tr')
		for each_proxy in proxys:
			item = ProxyItem()
			try:
				item['proxyip'] = each_proxy.xpath('./td[1]/text()').extract()[0]
				item['proxyport'] = each_proxy.xpath('./td[2]/text()').extract()[0]
				item['address'] = each_proxy.xpath('./td[6]/text()').extract()[0]
				item['type'] = each_proxy.xpath('./td[4]/text()').extract()[0]
				item['source'] = 'kuaidaili'
			except Exception:
				pass
			yield item
	
	# 66地区性免费代理网
	def sixip_area_parse(self, response):
		# 获取代理的信息
		proxys = response.xpath('//div[@id="footer"]/div/*/tr[position()>1]')
		for each_proxy in proxys:
			item = ProxyItem()
			try:
				item['proxyip'] = each_proxy.xpath('./td[1]/text()').extract()[0]
				item['proxyport'] = each_proxy.xpath('./td[2]/text()').extract()[0]
				item['address'] = each_proxy.xpath('./td[3]/text()').extract()[0]
				item['type'] = 'HTTP'
				item['source'] = '66ip'
			except Exception:
				pass
			yield item
	
	# 66全国免费代理网
	def sixip_parse(self, response):
		# 获取代理的信息
		proxys = response.xpath('//*[@id="main"]/div/div[1]/table/tr[position()>1]')
		for each_proxy in proxys:
			item = ProxyItem()
			try:
				item['proxyip'] = each_proxy.xpath('./td[1]/text()').extract()[0]
				item['proxyport'] = each_proxy.xpath('./td[2]/text()').extract()[0]
				item['address'] = each_proxy.xpath('./td[3]/text()').extract()[0]
				item['type'] = 'HTTP'
				item['source'] = '66ip'
			except Exception:
				pass
			yield item
	
	# 云代理ip3366.net
	def yun_parse(self, response):
		# 获取代理的信息
		proxys = response.xpath('//tbody/tr')
		for each_proxy in proxys:
			item = ProxyItem()
			try:
				item['proxyip'] = each_proxy.xpath('./td[1]/text()').extract()[0]
				item['proxyport'] = each_proxy.xpath('./td[2]/text()').extract()[0]
				item['address'] = each_proxy.xpath('./td[6]/text()').extract()[0]
				item['type'] = each_proxy.xpath('./td[4]/text()').extract()[0]
				item['source'] = 'ip3366'
			except Exception:
				pass
			yield item
	
	# 360代理
	def swei360_parse(self, response):
		# 获取代理的信息
		proxys = response.xpath('//tbody/tr')
		for each_proxy in proxys:
			item = ProxyItem()
			try:
				item['proxyip'] = each_proxy.xpath('./td[1]/text()').extract()[0]
				item['proxyport'] = each_proxy.xpath('./td[2]/text()').extract()[0]
				item['address'] = each_proxy.xpath('./td[5]/text()').extract()[0]
				item['type'] = each_proxy.xpath('./td[4]/text()').extract()[0]
				item['source'] = 'swei360'
			except Exception:
				pass
			yield item

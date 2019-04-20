# -*- coding: utf-8 -*-
import logging
import random

import psycopg2
from scrapy.exceptions import IgnoreRequest
from twisted.internet.error import ConnectError, ConnectionRefusedError, TCPTimedOutError, TimeoutError
from twisted.web._newclient import ResponseNeverReceived

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
logger = logging.getLogger(__name__)


class ProxyMiddleware(object):
	# Not all methods need to be defined. If a method is not defined,
	# scrapy acts as if the downloader middleware does not modify the
	# passed objects.
	proxys = []
	
	def __init__(self):
		CNN = psycopg2.connect(database='testdb', user='postgres', password='cc903051', host='10.10.5.123', port='5432')
		CUR = CNN.cursor()
		sqlcmd = 'select * from proxy order by priority_level limit 50'
		CUR.execute(sqlcmd)
		rows = CUR.fetchall()
		for row in rows:
			self.proxys.append('http://' + row[0])
		
		CUR.close()
		CNN.close()
	
	def process_request(self, request, spider):
		# Called for each request that goes through the downloader
		# middleware.
		
		# Must either:
		# - return None: continue processing this request
		# - or return a Response object
		# - or return a Request object
		# - or raise IgnoreRequest: process_exception() methods of
		#   installed downloader middleware will be called
		if (len(self.proxys) > 0):
			idx = int(random.random() * len(self.proxys))
			pro_adr = self.proxys[idx]
			logger.debug('USE PROXY -> %s' % (pro_adr,), extra={'spider': spider})
			request.meta['proxy'] = pro_adr
		
		request.meta['retry_times'] = request.meta.get('retry_times', 0)
		return None


class TimeoutErrorMiddleware(object):
	RETRY_ERRORS = (TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, TCPTimedOutError)
	TRYTIMES = {}  # proxy中重试的次数
	
	def _delete_proxy(self, proxy):
		self.TRYTIMES[proxy] = self.TRYTIMES.get(proxy, 0) + 1
		try:
			if (self.TRYTIMES.get(proxy, 0) > 3):  # 一个代理如果出现4次不能访问网页的情况，就删除
				ProxyMiddleware.proxys.remove(proxy)
				logger.info('DELETE PROXY -> %s' % (proxy,))
		except(ValueError):
			pass
	
	def process_exception(self, request, exception, spider):
		# Called when a download handler or a process_request()
		# (from other downloader middleware) raises an exception.
		
		# Must either:
		# - return None: continue processing this exception
		# - return a Response object: stops process_exception() chain
		# - return a Request object: stops process_exception() chain
		if isinstance(exception, self.RETRY_ERRORS):
			retries = request.meta.get('retry_times', 0) + 1
			if retries < 4:
				retryreq = request.copy()
				retryreq.meta['retry_times'] = retries
				retryreq.dont_filter = True  # 此请求不应由调度程序进行重复过滤
				self._delete_proxy(request.meta.get('proxy', 'N'))
				logger.debug('%s try %d times,again...' % (retryreq, retries), extra={'spider': spider})
				return retryreq
			else:
				logger.debug('%s is dead, skipping' % (request,), extra={'spider': spider})
				raise IgnoreRequest('%s is dead, skipping' % request)

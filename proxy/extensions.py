# -*- coding: utf-8 -*-
import logging
import time
import urllib.request
from atexit import register
from datetime import datetime
from threading import BoundedSemaphore, RLock, Thread

import psycopg2
from lxml import etree
from scrapy import signals

from .middlewares import ProxyMiddleware

MAX = 20  # 验证代理的最大线程数
CHECKED = 0  # 通过验证的IP总数
logger = logging.getLogger(__name__)


class MyExtension(object):
	def __init__(self, crawler):
		self.crawler = crawler
		self.url = 'http://www.ipdizhichaxun.com/'
		self.BASETIME = 0
		self.RUNNING = False
		self.checkthd = BoundedSemaphore(MAX)
		self.lock = RLock()
	
	@classmethod
	def from_crawler(cls, crawler):
		instance = cls(crawler.stats)
		crawler.signals.connect(instance._spider_opened, signal=signals.spider_opened)
		crawler.signals.connect(instance._spider_idle, signal=signals.spider_idle)
		crawler.signals.connect(instance._spider_closed, signal=signals.spider_closed)
		return instance
	
	def _spider_opened(self, spider):
		self.RUNNING = True
		t = Thread(target=self.__start_add_proxy, args=())
		t.setDaemon(True)
		t.start()
	
	def _spider_idle(self, spider):
		self.RUNNING = False
	
	def _spider_closed(self, spider, reason):
		time.sleep(5)  # 暂停一下，等ADD PROXY进程退出
		logger.info('爬虫工作完成，下面进行代理的验证工作...')
		self.__check_all_proxy()
	
	def __start_add_proxy(self):
		con = psycopg2.connect(database='testdb', user='postgres', password='cc903051', host='10.10.5.123', port='5432')
		cur = con.cursor()
		
		rq = urllib.request.Request(self.url)
		t1 = datetime.now()
		rq = urllib.request.urlopen(rq)
		text = etree.HTML(rq.read())
		t2 = datetime.now()
		self.BASETIME = int((t2 - t1).microseconds / 1000)  # 0:00:00.154009
		
		while self.RUNNING:
			sqlcmd = 'select * from proxy where priority_level=9'
			try:
				cur.execute(sqlcmd)
				rows = cur.fetchall()
				for row in rows:
					proxy_ip = row[0]
					if self.RUNNING:
						self.checkthd.acquire()
						t = Thread(target=self.__checkproxy, args=(proxy_ip, True))
						t.setDaemon(True)
						t.start()
					else:
						break
			except(Exception) as e:
				logger.error('__start_add_proxy: %s' % (str(e),))
		logger.debug('***********END ADD PROXY***********')
		
		cur.close()
		con.close()
		return
	
	def __check_all_proxy(self):
		con = psycopg2.connect(database='testdb', user='postgres', password='cc903051', host='10.10.5.123', port='5432')
		cur = con.cursor()
		
		# 清除所有代理设置
		proxy = urllib.request.ProxyHandler({})
		opener = urllib.request.build_opener(proxy)
		urllib.request.install_opener(opener)
		
		rq = urllib.request.Request(self.url)
		t1 = datetime.now()
		rq = urllib.request.urlopen(rq)
		text = etree.HTML(rq.read())
		t2 = datetime.now()
		self.BASETIME = int((t2 - t1).microseconds / 1000)  # 0:00:00.154009
		
		sqlcmd = 'select * from proxy where priority_level<99'
		try:
			cur.execute(sqlcmd)
			rows = cur.fetchall()
			logger.info('Total recorders: %d' % (len(rows),))
			for row in rows:
				proxy_ip = row[0]
				self.checkthd.acquire()
				t = Thread(target=self.__checkproxy, args=(proxy_ip, False))
				t.start()
		except(Exception) as e:
			logger.error('__start_check_proxy: %s' % (str(e),))
		cur.close()
		con.close()
		return
	
	# 验证代理IP有效性的方法
	def __checkproxy(self, proxy_ip, startflag):
		global CHECKED
		
		conn = psycopg2.connect(database='testdb', user='postgres', password='cc903051', host='10.10.5.123', port='5432')
		cur = conn.cursor()
		
		header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:51.0) Gecko/20100101 Firefox/51.0'}
		proxy = urllib.request.ProxyHandler({'http': proxy_ip})
		opener = urllib.request.build_opener(proxy)
		urllib.request.install_opener(opener)
		
		t1 = datetime.now()
		rq = urllib.request.Request(self.url)
		rq.add_header = [('User-Agent', header['User-Agent'])]
		try:
			rq = urllib.request.urlopen(rq, timeout=4)
			text = etree.HTML(rq.read())
			t2 = datetime.now()
			proxytime = (t2 - t1).seconds * 1000 + int((t2 - t1).microseconds / 1000)  # 毫秒
			ip = text.xpath('//p[@class="result"]/strong/span[1]/text()')[0]
			ip = ip.encode('utf-8').decode()
		
		except(Exception) as e:
			# logger.error("checkproxy error: %s" % (str(e),))
			sqlcmd = "update proxy set priority_level=99 where proxy_ip='" + proxy_ip + "'"
			cur.execute(sqlcmd)
			conn.commit()
		else:  # 如果没有异常发生，则执行这段代码
			if (ip == proxy_ip.split(':')[0]):  # 某些代理可以用，但最终检测出来的IP与代理IP地址不同
				delay = proxytime - self.BASETIME
				level = 0
				if (0 < delay <= 500):
					level = 1
				if (500 < delay <= 1500):
					level = 2
				if (1500 < delay <= 3000):
					level = 3
				if (3000 < delay < 5000):
					level = 4
				if (5000 <= delay):
					level = 5
				self.lock.acquire()
				if startflag:
					if level < 2:
						ProxyMiddleware.proxys.append('http://' + proxy_ip)
						logger.info('ADD PROXY -> %s' % (proxy_ip,))
				else:
					logger.info('CHECK PASS -> %s  LEVEL: %s' % (proxy_ip, str(level)))
					CHECKED = CHECKED + 1
				self.lock.release()
			else:
				level = 99
			
			sqlcmd = "update proxy set priority_level=" + str(level) + " where proxy_ip='" + proxy_ip + "'"
			cur.execute(sqlcmd)
			conn.commit()
		
		finally:
			self.checkthd.release()
			cur.close()
			conn.close()


@register
def exitfun():
	global CHECKED
	
	logger.info('代理验证工作完成！共计 %d 个' % (CHECKED,))
	CNN = psycopg2.connect(database='testdb', user='postgres', password='cc903051', host='10.10.5.123', port='5432')
	CUR = CNN.cursor()
	sqlcmd = 'delete from proxy  where priority_level=99'
	CUR.execute(sqlcmd)
	CNN.commit()
	CUR.close()
	CNN.close()
	return

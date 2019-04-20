import urllib.request
from atexit import register
from datetime import datetime
from threading import BoundedSemaphore, RLock, Thread

import psycopg2
from lxml import etree

MAX = 20
BASETIME = 0
checkthd = BoundedSemaphore(MAX)
lock = RLock()
url = 'http://www.ipdizhichaxun.com/'  # http://tool.pc360.net/ip/


# url = 'https://www.bejson.com/httputil/getip/'   # http://www.yii666.com/


# 验证代理IP有效性的方法
def checkproxy(proxy_ip, proxy_type):
	conn = psycopg2.connect(database="testdb", user="postgres", password="cc903051", host="10.10.5.123", port="5432")
	cur = conn.cursor()
	
	header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:51.0) Gecko/20100101 Firefox/51.0'}
	
	proxy = urllib.request.ProxyHandler({'http': proxy_ip})
	opener = urllib.request.build_opener(proxy)
	urllib.request.install_opener(opener)
	
	rq = urllib.request.Request(url)
	rq.add_header = [('User-Agent', header['User-Agent'])]
	ip = ''
	t1 = datetime.now()
	try:
		rq = urllib.request.urlopen(rq, timeout=5)
		context = rq.read()
		text = etree.HTML(context)
		t2 = datetime.now()
		proxytime = (t2 - t1).seconds * 1000 + int((t2 - t1).microseconds / 1000)  # 毫秒
		ip = text.xpath('//p[@class="result"]/strong/span[1]/text()')[0]
		ip = ip.encode('utf-8').decode()
	except(Exception) as e:
		# print(str(e))
		sqlcmd = "update proxy set priority_level=99 where proxy_ip='" + proxy_ip + "'"
		cur.execute(sqlcmd)
		conn.commit()
	else:
		if (ip == proxy_ip.split(':')[0]):
			delay = proxytime - BASETIME
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
			lock.acquire()
			print("CHECK PASS", end=" -> ")
			print(proxy_ip, end="  ")
			print("level: " + str(level))
			lock.release()
		else:
			level = 99
		sqlcmd = "update proxy set priority_level=" + str(level) + " where proxy_ip='" + proxy_ip + "'"
		cur.execute(sqlcmd)
		conn.commit()
	
	finally:
		checkthd.release()
		cur.close()
		conn.close()


CNN = psycopg2.connect(database="testdb", user="postgres", password="cc903051", host="10.10.5.123", port="5432")
CUR = CNN.cursor()


def main():
	rq = urllib.request.Request(url)
	t1 = datetime.now()
	rq = urllib.request.urlopen(rq)
	text = rq.read().decode("utf-8")
	t2 = datetime.now()
	BASETIME = int((t2 - t1).microseconds / 1000)  # 0:00:00.154009
	sqlcmd = "select * from proxy"  # where priority_level=5
	CUR.execute(sqlcmd)
	rows = CUR.fetchall()
	print('Total proxys: %d' % (len(rows),))
	for row in rows:
		proxy_ip = row[0]
		proxy_type = row[1]
		checkthd.acquire()
		t = Thread(target=checkproxy, args=(proxy_ip, proxy_type))
		t.start()


if __name__ == '__main__':
	main()


@register
def exitfun():
	print('----all threads done---')
	# sqlcmd = "delete from proxy  where priority_level=99"
	# CUR.execute(sqlcmd)
	# CNN.commit()
	CUR.close()
	CNN.close()

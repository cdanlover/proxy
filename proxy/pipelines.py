# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import psycopg2

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

logger = logging.getLogger(__name__)


class ProxyPipeline(object):
	def process_item(self, item, spider):
		conn = psycopg2.connect(database='testdb', user='postgres', password='cc903051', host='10.10.5.123', port='5432')
		cur = conn.cursor()
		# proxy_ip,type,address,insert_time,source[,priority_level]
		sqlcmd = 'INSERT INTO proxy VALUES (%s, %s, %s, %s, %s)'
		insert_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		try:
			proxyip = item['proxyip'] + ':' + item['proxyport']
			values = (proxyip, item['type'], item['address'], insert_time, item['source'])
			cur.execute(sqlcmd, values)
			conn.commit()
		except psycopg2.IntegrityError as e:
			if (str(e).find('proxy_pkey') != -1):
				pass
			else:
				logger.error('INSERT to db error! ' + str(e), extra={'spider': spider})
			conn.rollback()
		except KeyError:
			pass
		finally:
			cur.close()
			conn.close()
		return item

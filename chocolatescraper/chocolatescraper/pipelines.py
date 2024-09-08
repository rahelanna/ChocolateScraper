# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import mysql.connector
import psycopg2
from dotenv import load_dotenv
import os


class ChocolatescraperPipeline:
    def process_item(self, item, spider):
        return item


class PriceToUSDPipeline:
    gbpToUsdRate = 1.3

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if adapter.get('price'):
            float_price = float(adapter['price'])
            adapter['price'] = float_price * self.gbpToUsdRate

            return item
        else:
            raise DropItem(f"Missing price in {item}")


class DublicatesPipeline:

    def __init__(self):
        self.names_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if adapter['name'] in self.names_seen:
            raise DropItem(f"Duplicate item found: {item!r}")
        else:
            self.names_seen.add(adapter['name'])
            return item


class SaveToMySQLPipeline(object):

    def __init__(self):
        load_dotenv()
        self.conn = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'),
            port=os.getenv('port')
        )

        self.curr = self.conn.cursor()

        self.curr.execute("""
        CREATE TABLE IF NOT EXISTS chocolate_products(
            id int NOT NULL auto_increment PRIMARY KEY,
            name text,
            price DECIMAL,
            url VARCHAR(255)
        )
        """)
        self.conn.commit()

    def process_item(self, item, spider):
        self.store_db(item)
        return item

    def store_db(self, item):
        self.curr.execute(""" insert into chocolate_products (
        name,
        price,
        url
        ) values(
        %s,
        %s,
        %s)
        """, (
            item["name"],
            item["price"],
            item["url"]
        ))
        self.conn.commit()


class SaveToPostgresPipeline(object):

    def __init__(self):
        load_dotenv()
        self.conn = psycopg2.connect(
            dbname='${{ secrets.POSTGRES_DB }}',
            user='${{ secrets.POSTGRES_USER }}',
            password='${{ secrets.POSTGRES_PASSWORD }}',
            host='localhost',
            port=5432
        )

        self.curr = self.conn.cursor()

        self.curr.execute("""
        CREATE TABLE IF NOT EXISTS chocolate_products(
            id SERIAL PRIMARY KEY,
            name text,
            price DECIMAL,
            url VARCHAR(255)
        )
        """)

        self.conn.commit()

    def process_item(self, item, spider):
        self.store_db(item)
        return item

    def store_db(self, item):
        try:
            self.curr.execute(""" 
            INSERT INTO chocolate_products (name, price, url)
            VALUES(%s, %s, %s)
            """, (
                item["name"],
                item["price"],
                item["url"]
            ))
        except BaseException as e:
            print(e)
        self.conn.commit()

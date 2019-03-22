# -*- coding: utf-8 -*-
import scrapy


class UsStocksSpider(scrapy.Spider):
    name = 'US_Stocks'
    allowed_domains = ['www.marketwatch.com/tools/markets/stocks/country/united-states#']
    start_urls = ['http://www.marketwatch.com/tools/markets/stocks/country/united-states#/']

    def parse(self, response):
        pass

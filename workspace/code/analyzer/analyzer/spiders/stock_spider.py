import scrapy
import os
import datetime
from scrapy.selector import Selector 
from scrapy.http import HtmlResponse

class StockSpider(scrapy.Spider):
    name = "stock"
    urls = ['https://www.screener.in/company/TRENT/consolidated/']
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse_mine)

    def parse(self, response):
        page = response.url.split("/")[-3]
        today = datetime.datetime.now()
        #filename = 'stock_'+str(today.year)+'_'+str(today.month)+'_'+str(today.day)+'_'+page+'.txt'
        filename = 'stock_'+str(today.strftime('%Y_%h_%d'))+'_'+page+'.txt'
        os.chdir('output')
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)

    def parse_mine(self,response):
        page = response.url.split("/")[-3]
        today = datetime.datetime.now()
        #filename = 'stock_'+str(today.year)+'_'+str(today.month)+'_'+str(today.day)+'_'+page+'.txt'
        filename = 'stock_'+str(today.strftime('%Y_%h_%d'))+'_'+page+'.csv'
        os.chdir('output')
        with open(filename, 'w') as f:
            f.write(response.css('div#content-area div#company-info h1::text').get())
        #for post in response.css(div@con)
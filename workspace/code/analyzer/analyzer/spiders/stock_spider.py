import scrapy
import os
import shutil
import datetime
from scrapy.selector import Selector 
from scrapy.http import HtmlResponse
import re
from openpyxl import Workbook
from openpyxl import load_workbook
import pandas as pd

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
        os.chdir('file_processing')
        template_file = 'template\\excel_format.xlsx'
        dest_filename = 'output\\stock_'+today.strftime('%Y_%h_%d')+'_'+page+'.xlsx'
        workbook = load_workbook(filename=template_file)
        yearly_Sheet = workbook["Yearly"]
        #df_balance_sheet = self.importAsDataframe(section_id = 'balance-sheet')
        yearly_Sheet['A8'] = response.css('div#content-area div#company-info h1::text').get()
        yearly_Sheet['B8'] = response.css('#content-area > section:nth-child(5) > ul > li:nth-child(2) > b::text').get()
        #sheet.write(9,0,response.css('div#content-area div#company-info h1::text').get())
        #wb.save(dest_filename)
        workbook.save(dest_filename)

    def remove_html_tags(self,text):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def importAsDataframe(self, section_id,response):
        #response.css('#balance-sheet > div.responsive-holder > table > tbody').get()
        table = response.css('#'+section_id+' > div.responsive-holder > table').get()
        rows = table.xpath('//tr')
        for row in rows:
            row.xpath('td//text()')[0].extract()
            table = pd.DataFrame()
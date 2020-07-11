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
        with open('temporary_files\\'+filename, 'wb') as f:
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
        df_balance_sheet = self.importAsDataframe(section_id = 'balance-sheet',response=response)
        print(df_balance_sheet.head())
        #sheet.write(9,0,response.css('div#content-area div#company-info h1::text').get())
        #wb.save(dest_filename)
        workbook.save(dest_filename)

    def remove_html_tags(self,text):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def importAsDataframe(self, section_id,response):
        headers = response.xpath('//*[@id="'+section_id+'"]/div[2]/table/thead//text()').getall()
        tableBody = response.xpath('//*[@id="'+section_id+'"]/div[2]/table/tbody//text()').getall()
        with open('temporary_files\\'+section_id+'.csv', 'wb+') as f:
            header_row = 'category,'
            for header in headers:
                header_row = header_row +header.strip()+ ','
            header_row = header_row.replace(',,',',').replace(',,',',')
            f.write((header_row[:-1]+'\n').encode('utf-8'))
            col_count = 0
            header_length = len(header_row[:-1].split(',')) +1
            for rows in tableBody:
                    if rows.strip() == "":
                        continue
                    elif rows.strip() == '+':
                        continue
                    else :
                        rows = (' "'+rows+'" ,')
                        rows = re.sub(' +', ' ', rows)
                        rows = re.sub('\n+', '', rows)
                        rows = re.sub(' ', '', rows)
                        rows = re.sub(',,', ',', rows)
                        col_count  = (col_count + 1)%(header_length+1)
                        if col_count == header_length:
                            f.seek(-1, os.SEEK_END)
                            f.truncate()
                            f.write(('\n').encode('utf-8'))
                            col_count = 1
                        f.write(rows.encode('utf-8'))
            f.seek(-1, os.SEEK_END)
            f.truncate()
            f.close()
        df = pd.read_csv ('temporary_files\\'+section_id+'.csv',index_col=None)
        return df
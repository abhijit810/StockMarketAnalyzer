import scrapy
import os
import shutil
import datetime
import time
from scrapy.selector import Selector 
from scrapy.http import HtmlResponse
import re
from openpyxl import Workbook
from openpyxl import load_workbook
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

os.chdir('file_processing')

class StockSpider(scrapy.Spider):
    name = "stock"
    def __init__(self, **kwargs):
        today = datetime.datetime.now()
        self.companies = self.def_companies_df()
        self.company_codes = list(self.companies.index.values)
        self.template_file = 'template\\excel_format.xlsx'
        self.temporary_file = 'temporary_files\\temp_format.xlsx'
        self.dest_filename = 'output\\stock_'+today.strftime('%Y_%h_%d')+'_.xlsx'

    def start_requests(self):
        if(os.path.exists(self.temporary_file)):os.remove(self.temporary_file)
        shutil.copyfile(self.template_file, self.temporary_file)
        workbook = load_workbook(filename=self.temporary_file)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
        browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        source_Url = 'https://www.screener.in/'
        browser.get(source_Url)
        for count, company_code in enumerate(self.company_codes):
            url = self.getScreenerUrlSelenium(browser = browser , companyName = company_code)
            print('url :',url)
            yield scrapy.Request(url=url, callback=self.parseScreener, meta={'count':count+6, 'company_code':company_code, 'workbook':workbook})
        workbook.close()

    def parseScreener(self, response):
        count = str(response.meta['count'])
        company_code = str(response.meta['company_code'])
        workbook = response.meta['workbook']
        company = self.companies.loc[company_code]
        company_name = company['NAME OF COMPANY']
        sector_name = company['Industry']
        group = company['Group']
        cmp= response.css('#content-area > section:nth-child(5) > ul > li:nth-child(2) > b::text').get()
        yearly_Sheet = workbook["Yearly"]
        yearly_Sheet['A'+count] = company_name
        yearly_Sheet['B'+count] = sector_name
        yearly_Sheet['C'+count] = group
        yearly_Sheet['D'+count] = cmp
        workbook.save(self.temporary_file)
        if(os.path.exists(self.dest_filename)): os.remove(self.dest_filename)
        if(os.path.exists(self.temporary_file)): shutil.copyfile(self.temporary_file, self.dest_filename)

    def importAsDataframe(self, section_id,comapny_name,response):
        headers = response.xpath('//*[@id="'+section_id+'"]/div[2]/table/thead//text()').getall()
        tableBody = response.xpath('//*[@id="'+section_id+'"]/div[2]/table/tbody//text()').getall()
        with open('temporary_files\\'+comapny_name+'_'+section_id+'.csv', 'wb+') as f:
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
    
    def def_companies_df(self):
        '''reads the raw datasets and returns the desired dataframe with useful columns'''
        NSE = pd.read_csv ('template\\NSE_list_of_companies.csv',index_col='SYMBOL')
        NSE = NSE.rename(columns={"SYMBOL": "SECURITY"})

        BSE = pd.read_csv ('template\\BSE_list_of_companies.csv',index_col='Security Id')
        BSE = BSE.rename(columns={"Security Id": "SECURITY"})

        companies_df = pd.concat([NSE, BSE],axis=1)
        return companies_df[['NAME OF COMPANY','Industry','Group']].head(15)

    def getScreenerUrlSelenium(self, browser , companyName):
        initial_url = browser.current_url
        serachBoxXpath = '//*[@id="top-nav-search"]/div/input'
        while(True):
            if(browser.current_url != initial_url):
                return browser.current_url
            else:
                browser.find_element_by_xpath(serachBoxXpath).send_keys("",companyName)
                browser.find_element_by_xpath(serachBoxXpath).send_keys(Keys.ENTER)
#df_balance_sheet = self.importAsDataframe(section_id = 'balance-sheet',comapny_name=comapny_name,response=response)
#print(df_balance_sheet.head())
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
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import mechanicalsoup

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
        #scraping screener
        sbrowser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        ScreenerSource_Url = 'https://www.screener.in/'
        sbrowser.get(ScreenerSource_Url)
        #scraping moneycontrol
        MoneyControlSourceurl = 'http://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str=&topsearch_type=1&search_str=trent'
        mbrowser = mechanicalsoup.StatefulBrowser(user_agent='MechanicalSoup')
        mbrowser.open(MoneyControlSourceurl)
        for count, company_code in enumerate(self.company_codes):
            screenerUrl = self.getScreenerUrlSelenium(browser = sbrowser , companyName = company_code)
            MoneyControlurl = self.getMoneyControlUrl(browser = mbrowser , companyName = company_code)
            if screenerUrl is not None :
                yield scrapy.Request(url=screenerUrl, callback=self.parseScreener, meta={'count':count+6, 'company_code':company_code, 'workbook':workbook})
            if MoneyControlurl is not None:
                yield scrapy.Request(url=MoneyControlurl, callback=self.parseMoneyControl, meta={'count':count+6, 'company_code':company_code, 'workbook':workbook})
            if screenerUrl is None or MoneyControlurl is None :
                self.CompanyNotFound(count+6, company_code, workbook, screenerUrl, MoneyControlurl)
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
        market_cap = response.css('#content-area > section:nth-child(5) > ul > li:nth-child(1) > b::text').get()
        yearly_Sheet = workbook["Yearly"]
        yearly_Sheet['A'+count] = company_name
        yearly_Sheet['B'+count] = sector_name
        yearly_Sheet['C'+count] = group
        yearly_Sheet['D'+count] = market_cap + ' Cr'
        yearly_Sheet['E'+count] = cmp
        workbook.save(self.temporary_file)
        if(os.path.exists(self.dest_filename)): os.remove(self.dest_filename)
        if(os.path.exists(self.temporary_file)): shutil.copyfile(self.temporary_file, self.dest_filename)

    def parseMoneyControl(self, response):
        count = str(response.meta['count'])
        print(count)
        company_code = str(response.meta['company_code'])
        workbook = response.meta['workbook']
        company = self.companies.loc[company_code]
        company_name = company['NAME OF COMPANY']
        sector_name = company['Industry']
        group = company['Group']
        print('MoneyControl',company_name,sector_name,group)
        yearly_Sheet = workbook["Yearly"]
        print(yearly_Sheet)
        workbook.save(self.temporary_file)
        if(os.path.exists(self.dest_filename)): os.remove(self.dest_filename)
        if(os.path.exists(self.temporary_file)): shutil.copyfile(self.temporary_file, self.dest_filename)

    def CompanyNotFound(self, count, company_code, workbook, screenerUrl, MoneyControlurl):
        count = str(count)
        company = self.companies.loc[company_code]
        company_name = company['NAME OF COMPANY']
        sector_name = company['Industry']
        group = company['Group']
        cmp= "Not Found"
        yearly_Sheet = workbook["Yearly"]
        yearly_Sheet['A'+count] = company_name
        yearly_Sheet['B'+count] = sector_name
        yearly_Sheet['C'+count] = group
        if screenerUrl is None : yearly_Sheet['E'+count] = cmp
        if MoneyControlurl is None :pass
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
        retries = 0
        while(True):
            if(browser.current_url != initial_url):
                return browser.current_url
            else:
                if (retries < 20) :
                    browser.find_element_by_xpath(serachBoxXpath).clear()
                    browser.find_element_by_xpath(serachBoxXpath).send_keys("",companyName)
                    browser.find_element_by_xpath(serachBoxXpath).send_keys(Keys.ENTER)
                    retries = retries + 1
                else :
                    return None

    def getMoneyControlUrl(self, browser, companyName):
        browser.select_form()
        browser['search_str'] = companyName
        browser.submit_selected()
        form_list = str(browser.get_current_page())
        if form_list.find("Sorry, there are no matches for your search") != -1 : return None
        if form_list.find("Search results") != -1 : 
            links = browser.get_current_page().findAll('a', attrs={'href': re.compile("^http://www.moneycontrol.com/")})
            for link in links :
                if '/'+companyName.lower()+'/' in link.get('href'):
                    return link.get('href')
        return browser.get_url()
#df_balance_sheet = self.importAsDataframe(section_id = 'balance-sheet',comapny_name=comapny_name,response=response)
#print(df_balance_sheet.head())
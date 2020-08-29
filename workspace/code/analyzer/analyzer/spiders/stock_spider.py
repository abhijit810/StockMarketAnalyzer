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
        self.metadata_df = self.def_GetMetadataDF()

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
        mbrowser = mechanicalsoup.StatefulBrowser(user_agent='MechanicalSoup')
        for count, company_code in enumerate(self.company_codes):
            screenerUrl = self.getScreenerUrlSelenium(browser = sbrowser , companyName = company_code)
            MoneyControlurl = self.getMoneyControlUrl(browser = mbrowser , companyName = company_code)
            self.updateWorkbookFromDf( workbook, count+6, company_code )
            if screenerUrl is not None :
                yield scrapy.Request(url=screenerUrl, callback=self.parseScreener, meta={'count':count+6, 'workbook':workbook})
            if MoneyControlurl is not None:
                yield scrapy.Request(url=MoneyControlurl, callback=self.parseMoneyControl, meta={'count':count+6, 'workbook':workbook})
            if screenerUrl is None or MoneyControlurl is None :
                pass
                #self.CompanyNotFound(count+6, company_code, workbook, screenerUrl, MoneyControlurl)
            workbook.close()

    def parseScreener(self, response):
        count = str(response.meta['count'])
        workbook = response.meta['workbook']
        fromScreener_df = self.metadata_df[ self.metadata_df['source'] == 'screener']
        yearly_Sheet = workbook["Yearly"]
        # add your scraping code here 
        for index in fromScreener_df.index:
            metric_css = fromScreener_df["scrape_address_css"].loc[index]
            if metric_css is not None:
                yearly_Sheet[index + count] = response.css(metric_css).get()
            else:
                metric_xpath = fromScreener_df["scrape_address_xpath"].loc[index]
                yearly_Sheet[index + count] = response.xpath(metric_xpath).get()
        self.def_postRowProcessing(workbook)

    def parseMoneyControl(self, response):
        count = str(response.meta['count'])
        workbook = response.meta['workbook']
        fromMoneycontrol_df = self.metadata_df[ self.metadata_df['source'] == 'moneycontrol']
        yearly_Sheet = workbook["Yearly"]
        # add your scraping code here 
        for index in fromMoneycontrol_df.index:
            metric_css = fromMoneycontrol_df["scrape_address_css"].loc[index]
            if metric_css is not None:
                yearly_Sheet[index + count] = response.css(metric_css).get()
            else:
                metric_xpath = fromMoneycontrol_df["scrape_address_xpath"].loc[index]
                yearly_Sheet[index + count] = response.xpath(metric_xpath).get()
        print(yearly_Sheet)
        self.def_postRowProcessing(workbook)

    def CompanyNotFound(self, count, company_code, workbook, screenerUrl, MoneyControlurl):
        pass

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
        MoneyControlSourceurl = 'http://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str=&topsearch_type=1&search_str=trent'
        browser.open(MoneyControlSourceurl)
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
        if form_list.find("No result found for") != -1 : return None
        print(companyName.lower().split()[0])
        if form_list.find(companyName.lower().split()[0]) != -1 :
            return browser.get_url()
        else: return None

    def def_GetMetadataDF(self):
        '''reads the metadata csv file'''
        return pd.read_csv ('metadata\\metadata.csv',index_col= 'Excel_col_code' )

    def updateWorkbookFromDf(self, workbook, count, company_code):
        '''updates values in excel workbook for  the columns being taken from DF'''
        fromMetadataDF = self.metadata_df[ self.metadata_df['source'] == 'companies_df']
        yearly_Sheet = workbook["Yearly"]
        for index in fromMetadataDF.index:
            company = self.companies.loc[company_code]
            yearly_Sheet[index + str(count)] = company[ fromMetadataDF["col_name_in_comp_df"].loc[index] ]
        self.def_postRowProcessing(workbook)

    def def_postRowProcessing(self, workbook):
        '''this function does all the workbook saving and post processing part'''
        workbook.save(self.temporary_file)
        if(os.path.exists(self.dest_filename)): os.remove(self.dest_filename)
        if(os.path.exists(self.temporary_file)): shutil.copyfile(self.temporary_file, self.dest_filename)
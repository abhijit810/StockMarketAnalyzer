import pandas as pd
import os
import time
import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from robobrowser import RoboBrowser
import requests
from bs4 import BeautifulSoup
import urllib
import mechanicalsoup
#from selenium.webdriver.chrome.options import Options

os.chdir('file_processing')

def def_companies_df():

    NSE = pd.read_csv ('template\\NSE_list_of_companies.csv',index_col='SYMBOL')
    NSE = NSE.rename(columns={"SYMBOL": "SECURITY"})

    BSE = pd.read_csv ('template\\BSE_list_of_companies.csv',index_col='Security Id')
    BSE = BSE.rename(columns={"Security Id": "SECURITY"})
    
    companies_df = pd.concat([NSE, BSE],axis=1)
    return companies_df[['NAME OF COMPANY','Industry','Group']]


def getMoneyControlUrl(companyName):
    source_Url = 'http://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str=&topsearch_type=1&search_str=trent'
    mbrowser = mechanicalsoup.StatefulBrowser(user_agent='MechanicalSoup')
    mbrowser.open(source_Url)
    mbrowser.select_form()
    mbrowser['search_str'] = companyName
    mbrowser.submit_selected()
    form_list = str(mbrowser.get_current_page())
    if form_list.find("Sorry, there are no matches for your search") != -1 : return None
    if form_list.find("Search results") != -1 : 
        links = mbrowser.get_current_page().findAll('a', attrs={'href': re.compile("^http://www.moneycontrol.com/")})
        for link in links :
            if '/'+companyName.lower()+'/' in link.get('href'):
                return link.get('href')
    return mbrowser.get_url()


def getScreenerUrlSelenium(companyName = "None"):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    source_Url = 'http://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str=&topsearch_type=1&search_str=trent'
    browser.get(source_Url)
    browser.find_element_by_xpath(""" //*[@id="content-area"]/div/div/div/div/input """).send_keys("",companyName)
    browser.find_element_by_xpath(""" //*[@id="content-area"]/div/div/div/div/input """).send_keys(Keys.ENTER)
    return browser.current_url
    

def getURLrobo():
    
    source_Url = 'https://www.screener.in/'
    rbrowser = RoboBrowser(history=True, parser="lxml")
    rbrowser.open(source_Url)
    form = rbrowser.get_form(xpath="""//*[@id="top-nav-search"]/div/input""")
    print(form)

def getURLMixed():
    source_Url = 'https://www.screener.in/'
    mbrowser = mechanicalsoup.StatefulBrowser(user_agent='MechanicalSoup')
    rbrowser = RoboBrowser(history=True, parser="lxml")
    mbrowser.open(source_Url)
    rbrowser.open(source_Url)
    form = mbrowser.select_form('#top-nav-search')
    rbrowser.submit_form(form)

def newfunc():
    url = 'https://www.screener.in/'
    start = requests.session()
    open = start.get(url)
    #rb =  RoboBrowser(history=True, parser="html.parser")
    #print(open.headers)
    start.headers = open.headers
    rb = RoboBrowser(session=start,history=True, parser="html.parser")
    rb.open(url)
    #ff = rb.get_form(class_='u-full-width')
    #ff = rb.get_form(id=re.compile("top-nav-search"))
    ff = rb.get_forms()[0]
    print(ff)
    # yInputControl = rb.find(class_=re.compile(r'\y-input__control\b'))
    yInputControl = rb.find(placeholder="Company search...")
    #print(yInputControl)
    yInputControl.value = 'PCPL' 
    #rb.submit_form()

def usingurllib():
    url = 'https://www.screener.in/'
    rb =  RoboBrowser(history=True, parser="html.parser")
    rb.open(url)
    f = { rb.find(placeholder="Company search...").value : 'PCPL'}
    post_args = urllib.parse.urlencode(f)
    fp = urllib.request.urlopen(url, post_args)
    soup = BeautifulSoup(fp)
    print(soup)

def getMoneycontrolUrlSelenium(companyName = "None"):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    source_Url = 'https://www.moneycontrol.com/'
    browser.get(source_Url)
    browser.find_element_by_xpath(""" //*[@id="search_str"] """).send_keys("",companyName)
    browser.find_element_by_xpath(""" //*[@id="autosuggestlist"]/ul/div/div/li[1]/a """).click()
    return browser.current_url

def def_GetMetadataDF():
    '''reads the metadata csv file'''
    metadata_df = pd.read_csv ('metadata\\metadata.csv',index_col= 'Excel_col_code' )
    fromMetadataDF = metadata_df[ metadata_df['source'] == 'companies_df']
    print(fromMetadataDF)

def_GetMetadataDF()
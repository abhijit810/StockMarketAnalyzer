import scrapy

class StockSpider(scrapy.Spider):
    name = "stock"

    def start_requests(self):
        urls = [
            'https://www.screener.in/company/TRENT/consolidated/'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = 'quotes-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
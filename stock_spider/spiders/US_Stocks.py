# -*- coding: utf-8 -*-
import scrapy
import math

''' 
Scraping financial data for some stock (as default TSLA). Then, calculating bankruptcy likelihood with o-score. 
Yields values of financial datapoints needed in Ohlson O-score calulation, also the O-score itself. 
These values can then be outputted to a file, for example.
'''

class UsStocksSpider(scrapy.Spider):
    name = 'US_Stocks'
    tickers = ['TSLA']
    allowed_domains = ['marketwatch.com']
    start_urls = ['https://www.marketwatch.com/investing/stock/' + tickers[0] + '/financials']


    def parse(self, response):
        # start parsing from "financials" - path
        net_income_selectors = response.xpath('//*[@class="totalRow"]//*[@class="valueCell"]') 


        # if net_income is positive the selector below exists (list not empty)
        net_income_last = net_income_selectors[-1].xpath('./text()').extract()
        
        # if above does not exist (meanin negative net income)
        if not net_income_last:
            net_income_last = net_income_selectors[-1].xpath('./span/text()').extract()

        # same procedure for net_income_before_last
        # if net_income is positive the selector below exists (list not empty)
        net_income_before_last = net_income_selectors[-2].xpath('./text()').extract()
        
        # if above does not exist (meaning negative net income)
        if not net_income_before_last:
            net_income_before_last = net_income_selectors[-2].xpath('./span/text()').extract()
    
        # Yielding values as meta, to be used later in Ohlson O-score calculation
        balance_sheet_url = "/balance-sheet"
        yield scrapy.Request((response.url + balance_sheet_url), 
                            callback=self.parse_balance_sheet, 
                            meta = {'net_income_last': net_income_last[0], 
                                    'net_income_before_last': net_income_before_last[0]} )


    def parse_balance_sheet(self, response):
        # continue parsing to financials/balance-sheet
        net_income_last = response.meta['net_income_last']
        net_income_before_last = response.meta['net_income_before_last']
        
        total_assets = response.xpath('//*[@class="totalRow"]')[0].xpath('.//*[@class="valueCell"]/text()').extract()
        total_assets_last = total_assets[-1]

        total_liabilities = response.xpath('//*[@class="totalRow"]')[1].xpath('.//*[@class="valueCell"]/text()').extract()
        total_liabilities_last = total_liabilities[-1]

        current_assets = response.xpath('//*[@class="partialSum"]')[0].xpath('.//*[@class="valueCell"]/text()').extract()
        current_assets_last = current_assets[-1]

        current_liabilities = response.xpath('//*[@class="partialSum"]')[1].xpath('.//*[@class="valueCell"]/text()').extract()
        current_liabilities_last = current_liabilities[-1]

        yield scrapy.Request((self.start_urls[0] + "/cash-flow"),
                            callback= self.parse_cashflow,
                            meta =  {'net_income_last': net_income_last,
                                    'net_income_before_last': net_income_before_last,
                                    'total_assets_last': total_assets_last,
                                    'total_liabilities_last': total_liabilities_last,
                                    'current_assets_last': current_assets_last,
                                    allowed_domains'current_liabilities_last': current_liabilities_last})
    allowed_domains
    def parse_cashflow(self, responsallowed_domainse):
        # continue parsing to cash fallowed_domainslow statements sheet
        net_income_last = response.mallowed_domainseta['net_income_last']
        net_income_before_last = resallowed_domainsponse.meta['net_income_before_last']
        total_assets_last = responseallowed_domains.meta['total_assets_last']
        total_liabilities_last = response.meta['total_liabilities_last']
        current_assets_last = response.meta['current_assets_last']
        current_liabilities_last = response.meta['current_liabilities_last']

        funds_from_operations = response.xpath('//*[@class="partialSum"]')[0].xpath('.//*[@class="valueCell"]/text()').extract()
        funds_from_operations_last = funds_from_operations[-1]

        oscore = calculate_oscore(net_income_last, net_income_before_last, total_assets_last, total_liabilities_last, current_assets_last, current_liabilities_last, funds_from_operations_last)

        yield {'net_income_last': net_income_last,
                'net_income_before_last':net_income_before_last,
                'total_assets_last': total_assets_last,
                'total_liabilities_last': total_liabilities_last,
                'current_assets_last': current_assets_last,
                'current_liabilities_last': current_liabilities_last,
                'funds_from_operations_last': funds_from_operations_last,
                'oscore': oscore
                }

def format_values(value):
    """
    Helper function to change data from marketwatch - like string "(30M)" - meaning negative 30 million to number form. 
    """

    # initializing multiplier to 1, (used later on to change the number value 
    # according to last letter (M - million or B - billion))
    multiplier = 1

    # remove ( and ) if present, and change to negative value
    if (isinstance(value, str)):
        if (value.rfind('(')!= -1):
            value = value.replace("(", "")
            value = value.replace(")", "")
            # remove "M" or "B" from the end of string if present and change the value accordingly
            if value[-1] == "M":
                value = value.replace("M", "")
                multiplier = 1000000
            if value[-1] == "B":
                value = value.replace("B", "")
                multiplier = 1000000000
            return -1*float(value)*multiplier
        else:
            # remove "M" or "B" from the end of string if present and change the value accordingly
            if value[-1] == "M":
                value = value.replace("M", "")
                multiplier = 1000000
            if value[-1] == "B":
                value = value.replace("B", "")
                multiplier = 1000000000
            return float(value)*multiplier
    return float(value)

def calculate_oscore(net_income_last, net_income_before_last, total_assets_last, total_liabilities_last, current_assets_last, current_liabilities_last, funds_from_operations_last):
    """
    Helper function to calculate o-score for bankruptcy risk.
    O-scores of magnitude larger than 0.5 suggests that the firm will default within two years.
    """

    net_income_last = format_values(net_income_last)
    net_income_before_last = format_values(net_income_before_last)
    net_income_before_last = format_values(net_income_before_last)
    total_assets_last= format_values(total_assets_last)
    total_liabilities_last= format_values(total_liabilities_last)
    current_assets_last = format_values(current_assets_last)
    current_liabilities_last = format_values(current_liabilities_last)
    funds_from_operations_last = format_values(funds_from_operations_last)

    # calculating the "X" which is 1 if total liabilities exceed total assets, otherwise 0
    if total_liabilities_last > total_assets_last:
        X = 1
    else:
        X = 0
    
    # calculating the "Y" which is 1 if a net loss for the last two years, 0 otherwise
    if (net_income_before_last < 0) and (net_income_last < 0):
        Y = 1
    else:
        Y = 0 
    
    x1 = -1.32
    x2 = -0.407 * (math.log(total_assets_last))
    x3 = 6.03 * (total_liabilities_last / total_assets_last)
    x4 = -1.43 * ( (current_assets_last - current_liabilities_last) / total_assets_last)
    x5 = 0.0757 * (current_liabilities_last / current_assets_last)
    x6 = -1.72 * X
    x7 = -2.37 * (net_income_last / total_assets_last)
    x8 = -1.83 * (funds_from_operations_last / total_liabilities_last)
    x9 = 0.285 * Y
    x10 = -0.521 * ((net_income_last - net_income_before_last) / (net_income_last + net_income_before_last))

    oscore = float(x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10)

    return oscore
 
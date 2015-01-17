"""
CSIL Sourcing Module documentation (:mod:`sourcing.csil`)
=========================================================
"""

import vendors

import splinter
import time
import locale
from collections import OrderedDict

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

exparams = {
    'pcbname': 'Test',
    'layers': 2,
    'dX': '98.2',
    'dY': '46.7',
    'qty': range(100),
    'time': 15,     # 5, 7, 10, 12, 15, 18, 21, 25, 30
    'finish': 'Au', # HAL, Ag, Au, PBFREE, NP, I, OC
}


def get_csil_prices(params=exparams):
    delivery_codes = {
        5: '5#334',
        7: '7#529',
        10: '10#1452',
        12: '12#7271',
        15: '15#1453',
        18: '18#7272',
        21: '21#7273',
        25: '25#1455',
        30: '30#1642'
    }

    layers_codes = {
        1: '2180',
        2: '2181',
        4: '2183',
        6: '2184',
    }

    browser = splinter.Browser()
    url = 'http://www.pcbpower.com:8080'
    browser.visit(url)
    values = {
        'ctl00$ContentPlaceHolder1$txtUserName':'quazartech',
        'ctl00$ContentPlaceHolder1$txtPassword':'qt55655154'
    }
    browser.fill_form(values)
    button = browser.find_by_name('ctl00$ContentPlaceHolder1$btnlogin')
    button.click()
    link = browser.find_by_id('ctl00_aPlaceOrder')
    link.click()
    try:
        values = OrderedDict()
        values['ctl00$ContentPlaceHolder1$txtPCBName'] = params['pcbname']
        values['ctl00$ContentPlaceHolder1$ddlLayers'] = layers_codes[params['layers']]
        values['ctl00$ContentPlaceHolder1$txtDimX'] = params['dX']
        values['ctl00$ContentPlaceHolder1$txtDimY'] = params['dY']
        values['ctl00$ContentPlaceHolder1$txtQuantity'] = str(params['qty'][1])
        values['ctl00$ContentPlaceHolder1$DDLsurfacefinish'] = params['finish']
        values['ctl00$ContentPlaceHolder1$ddlDelTerms'] = delivery_codes[params['time']]
    except KeyError:
        raise ValueError

    if not browser.is_element_present_by_id('shortNotiText', wait_time=10):
        raise Exception
    ready = False
    timeout = 10
    while not ready and timeout:
        el = browser.find_by_id('shortNotiText')
        if el[0].text == u"We're online":
            ready = True
        timeout -= 1
        time.sleep(1)
    time.sleep(5)
    browser.fill_form(values)

    browser.fill_form(values)

    try:
        oldt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
    except AttributeError:
        oldt = ''
    qty = str(params['qty'][1])
    oldv = qty
    time.sleep(2)
    button = browser.find_by_id('ctl00_ContentPlaceHolder1_btnCalculate')

    button.click()
    time.sleep(2)
    button = browser.find_by_id('ctl00_ContentPlaceHolder1_btnCalculate')

    button.click()

    try:
        newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
    except AttributeError:
        newt = ''
    while oldt == newt:
        try:
            newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
        except AttributeError:
            newt = ''
        time.sleep(0.5)
    unitprice = locale.atof(newt)
    rval = {int(qty): unitprice}
    oldt = newt

    for qty in params['qty'][2:]:
        time.sleep(5)

        for char in oldv:
            browser.type('ctl00$ContentPlaceHolder1$txtQuantity', '\b')
            time.sleep(0.1)
        browser.type('ctl00$ContentPlaceHolder1$txtQuantity', str(qty))
        time.sleep(0.1)
        browser.type('ctl00$ContentPlaceHolder1$txtQuantity', '\t')
        time.sleep(0.1)
        print 'Waiting for ... ' + str(qty)
        oldv = str(qty)
        time.sleep(2)
        try:
            newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
        except AttributeError:
            newt = ''
        while oldt == newt and newt is not '':
            time.sleep(0.5)
            try:
                newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
            except AttributeError:
                newt = ''

        unitprice = locale.atof(newt)
        rval[qty] = unitprice
        oldt = newt

    browser.quit()
    return rval


class VendorCSIL(vendors.VendorBase):
    def __init__(self, name, dname, pclass):

        self._devices = ['PCB']
        super(VendorCSIL, self).__init__(name, dname, pclass)

    def search_vpnos(self, ident):
        pass

    def get_vpart(self, vpartno, ident=None):
        pass

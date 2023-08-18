import json
import logging
import pprint
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
from pydantic import BaseModel
import httpx

import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"

def check_settings(config, hass):
    if not any(config.get(i) for i in ["username"]):
        _LOGGER.error("username was not set")
    else:
        return True
        
    if not config.get("password"):
        _LOGGER.error("password was not set")
    else:
        return True

    raise vol.Invalid("Missing settings to setup the sensor.")

class Http2Client:
    def __init__(self, country):
        self.client = httpx.Client(http2=True)
        self.client.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Origin": f"https://my.youfone.{country.lower()}",
            "Referer": f"https://my.youfone.{country.lower()}/login",
            "Accept-Language": f"en-US,en;q=0.9"
        })

    def fetch_data(self, url):
        response = self.client.get(url, timeout=10)
        return response

    def post_data(self, url, data):
        response = self.client.post(url, content=data, timeout=30)
        return response

    def __del__(self):
        self.client.close()

class ComponentSession(object):
    def __init__(self, country):
        self.s = httpx.Client(http2=True)
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        self.s.headers["Referer"] = f"https://my.youfone.{country.lower()}/login"
        self.s.headers["Origin"] = f"https://my.youfone.{country.lower()}"
        # self.s.headers["Sec-Ch-Ua"] = f'"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"'
        # self.s.headers["Sec-Ch-Ua-Platform"] = f'"Windows"'
        # self.s.headers["Sec-Ch-Ua-Mobile"] = f'?0'
        # self.s.headers["Sec-Fetch-Dest"] = f'empty'
        # self.s.headers["Sec-Fetch-Mode"] = f'cors'
        # self.s.headers["Sec-Fetch-Site"] = f'same-origin'
        # self.s.headers["Accept-Language"] = f'en-US,en;q=0.9'
        self.userdetails = None
        self.msisdn = dict()
        self.customerid = dict()
        self._country = country.lower()
        self.loginSecurityKey = ""

    def login(self, username, password):
    # https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/login, POST
    # example payload
    # {
      # "request": {
        # "Login": "sdlkfjsldkfj@gmail.com",
        # "Password": "SDFSDFSDFSDFSDF"
      # }
    # }
    # example response: 
    # {"Message":"Authorization succes","ResultCode":0,"Object":{"Customer":{"CustomerNumber":9223283432,"Email":"eslkdjflksd@gmail.com","FirstName":"slfjs","Gender":null,"Id":3434,"Initials":"I","IsBusinessCustomer":false,"Language":"nl","LastName":"DSFSDF","PhoneNumber":"0412345678","Prefix":null,"RoleId":2},"Customers":[{"CustomerId":12345,"CustomerNumber":1234567890,"IsDefaultCustomer":true,"Msisdn":32412345678,"ProvisioningTypeId":1,"RoleId":2}],"CustomersCount":1}}
        # Get OAuth2 state / nonce

        # client = Http2Client(self._country)

        # login_page_url = f"https://my.youfone.{self._country}/login"
        # response1 = client.fetch_data(login_page_url)
        # _LOGGER.debug(f"response1: {response1.text}")
        # _LOGGER.debug("youfone.be login get result status code: " + str(response1.status_code) + ", response: " + response1.text)

        # login_page_url = "https://api.youfone.be/api/getPageBlocks?page_url=/login"
        # response1 = client.fetch_data(login_page_url)
        # _LOGGER.debug(f"response1: {response1.text}")
        # _LOGGER.debug("youfone.be login get result status code: " + str(response1.status_code) + ", response: " + response1.text)

        # login_url = "https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/login"
        # login_data = '{"request": {"Login": "' + username + '", "Password": "' + password + '", "remember_me": "false"}}'
        # response2 = client.post_data(login_url, data=login_data)
        # _LOGGER.debug(f"response2: {response2.text}")
        # response = response2
        # _LOGGER.debug("youfone.be login post result status code: " + str(response.status_code) + ", response: " + response.text)


        header = {"Content-Type": "application/json"}
        response = self.s.get(f"https://my.youfone.{self._country}/login",headers=header,timeout=30)
        _LOGGER.debug("youfone.be result status code: " + str(response.status_code) + ", response: " + response.text)
        response = self.s.get(f"https://my.youfone.{self._country}/assets/i18n/nl.json",headers=header,timeout=30)
        _LOGGER.debug("youfone.be result status code: " + str(response.status_code) + ", response: " + response.text)
        response = self.s.get(f"https://api.youfone.{self._country}/api/getPageBlocks?page_url=/login",headers=header,timeout=10)
        _LOGGER.debug("youfone.be result status code: " + str(response.status_code) + ", response: " + response.text)
        _LOGGER.debug(f"youfone.be cookeis: {self.s.cookies}")
        _LOGGER.debug(f"youfone.be response cookeis: {response.cookies}")
        for cookie in response.cookies:
            _LOGGER.debug(f"{cookie.name}: {cookie.value}")
        _LOGGER.debug("Headers:")
        for key, value in self.s.headers.items():
            _LOGGER.debug(f"{key}: {value}")
        response = self.s.post(f"https://my.youfone.{self._country}/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/login",content='{"request": {"Login": "'+username+'", "Password": "'+password+'", "remember_me": "false"}}',headers=header,timeout=30)


        _LOGGER.debug("youfone.be login post result status code: " + str(response.status_code) + ", response: " + response.text)
        _LOGGER.debug("youfone.be login header: " + str(response.headers))
        assert response.status_code == 200
        self.userdetails = response.json()
        for customer in self.userdetails.get('Object').get('Customers'):
            _LOGGER.debug(f"youfone.be Msisdn found: {customer.get('Msisdn')}")
            self.msisdn[customer.get('Msisdn')] = customer.get('Msisdn')
            self.customerid[customer.get('Msisdn')] = customer.get('CustomerId')
            _LOGGER.debug(f"youfone.be customerid: {customer.get('CustomerId')}, msisdn: {customer.get('Msisdn')}")
        _LOGGER.debug(f"youfone.be securitykey {response.headers.get('securitykey')}")
        self.s.headers["securitykey"] = response.headers.get('securitykey')
        self.loginSecurityKey = response.headers.get('securitykey')
        return self.userdetails

    def usage_details(self):
    # https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo
    # request.Msisdn - phonenr 
    # {"Message":null,"ResultCode":0,"Object":[{"Properties":[{"Key":"UsedAmount","Value":"0"},{"Key":"BundleDurationWithUnits","Value":"250 MB"},{"Key":"Percentage","Value":"0.00"},{"Key":"_isUnlimited","Value":"0"},{"Key":"_isExtraMbsAvailable","Value":"1"}],"SectionId":1},{"Properties":[{"Key":"UsedAmount","Value":"24"},{"Key":"BundleDurationWithUnits","Value":"200 Min"},{"Key":"Percentage","Value":"12.00"},{"Key":"_isUnlimited","Value":"0"}],"SectionId":2},{"Properties":[{"Key":"StartDate","Value":"1 februari 2023"},{"Key":"NumberOfRemainingDays","Value":"16"}],"SectionId":3},{"Properties":[{"Key":"UsedAmount","Value":"0.00"}],"SectionId":4}]}
        usage_details_data = dict()
        header = {"Content-Type": "application/json"}
        for msisdn in self.msisdn.keys():
            _LOGGER.debug(f"youfone.be before securitykey {self.s.headers['securitykey']}")
            self.s.headers["Referer"] = f"https://my.youfone.{self._country}/login"
            response = self.s.post(f"https://my.youfone.{self._country}/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetNotifications",content='{"request":{"CustomerId":'+str(self.customerid.get(msisdn))+'}}',headers=header,timeout=30)
            _LOGGER.debug("youfone.be GetNotifications result status code: " + str(response.status_code) + ", response: " + response.text)
            _LOGGER.debug(f"youfone.be securitykey {response.headers.get('securitykey')}")
            # self.s.headers["securitykey"] = response.headers.get('securitykey')
            self.s.headers["securitykey"] = self.loginSecurityKey
            self.s.headers["Referer"] = f"https://my.youfone.{self._country}/"
            _LOGGER.debug(f"youfone.be before securitykey {self.s.headers['securitykey']} params {str(msisdn)}, self.s.headers['Referer']: {self.s.headers['Referer']}")
            response = self.s.post(f"https://my.youfone.{self._country}/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo",content='{"request":{"Msisdn":'+str(msisdn)+'}}',headers=header,timeout=30)
            _LOGGER.debug("youfone.be GetOverviewMsisdnInfo result status code: " + str(response.status_code) + ", response: " + response.text)
            _LOGGER.debug(f"youfone.be securitykey {response.headers.get('securitykey')}")
            self.s.headers["securitykey"] = response.headers.get('securitykey')
            _LOGGER.debug("youfone.be  result status code: " + str(response.status_code) + ", msisdn: " + str(msisdn))
            _LOGGER.debug("youfone.be  result " + response.text)
            assert response.status_code == 200
            current_user_details = response.json()
            
            #fetch extra cost details
            response = self.s.post(f"https://my.youfone.{self._country}/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnExtraCosts",content='{"request":{"Msisdn":'+str(msisdn)+'}}',headers=header,timeout=30)
            _LOGGER.debug(f"youfone.be securitykey {response.headers.get('securitykey')}")
            self.s.headers["securitykey"] = response.headers.get('securitykey')
            _LOGGER.debug("youfone.be  result status code: " + str(response.status_code) + ", msisdn: " + str(msisdn))
            _LOGGER.debug("youfone.be  result " + response.text)
            assert response.status_code == 200
            current_user_details['extra'] = response.json()
            _LOGGER.debug(f"youfone.be  current_user_details {current_user_details}")
            usage_details_data[msisdn]= current_user_details
        return usage_details_data
        
    def subscription_details(self):
        subscription_details_data = dict()
        header = {"Content-Type": "application/json"}
        for msisdn in self.msisdn.keys():
            response = self.s.post(f"https://my.youfone.{self._country}/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetAbonnementMsisdnInfo",content='{"request": {"Msisdn": '+str(msisdn)+'}}',headers=header,timeout=30)
            _LOGGER.debug(f"youfone.be securitykey {response.headers.get('securitykey')}")
            self.s.headers["securitykey"] = response.headers.get('securitykey')
            _LOGGER.debug("youfone.be  result status code: " + str(response.status_code) + ", msisdn: " + str(msisdn))
            _LOGGER.debug("youfone.be  result " + response.text)
            assert response.status_code == 200
            jresponse = response.json()
            assert jresponse["ResultCode"] == 0
            obj = {}
            for section in jresponse["Object"]:
                obj[section["SectionId"]] = {}
                for prop in section["Properties"]:
                    obj[section["SectionId"]][prop["Key"]] = prop["Value"]
            subscription_details_data[msisdn] = obj
        return subscription_details_data
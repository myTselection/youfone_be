import json
import logging
import pprint
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
from pydantic import BaseModel

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
    if not config.get("data"):
        _LOGGER.error("data bool was not set")
    else:
        return True
    if not config.get("mobile"):
        _LOGGER.error("mobile bool was not set")
    else:
        return True
        
    if config.get("data") and config.get("mobile"):
        return True
    else:
        _LOGGER.error("At least one of data or mobile is to be set")

    raise vol.Invalid("Missing settings to setup the sensor.")


class ComponentSession(object):
    def __init__(self):
        # self.s = client
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Python/3"
        self.userdetails = None
        self.msisdn = None

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
        header = {"Content-Type": "application/json"}
        response = self.s.post("https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/login",data='{"Login": "'+username+'","Password": "'+password+'"}',headers=header,timeout=10)
        _LOGGER.debug("youfone.be login post result status code: " + str(response.status_code))
        assert response.status_code == 200
        self.userdetails = response.json()
        self.msisdn = self.userdetails.Object.Customers[0].Msisdn
        return self.userdetails

    def usage_details(self):
    # https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo
    # request.Msisdn - phonenr 
    # {"Message":null,"ResultCode":0,"Object":[{"Properties":[{"Key":"UsedAmount","Value":"0"},{"Key":"BundleDurationWithUnits","Value":"250 MB"},{"Key":"Percentage","Value":"0.00"},{"Key":"_isUnlimited","Value":"0"},{"Key":"_isExtraMbsAvailable","Value":"1"}],"SectionId":1},{"Properties":[{"Key":"UsedAmount","Value":"24"},{"Key":"BundleDurationWithUnits","Value":"200 Min"},{"Key":"Percentage","Value":"12.00"},{"Key":"_isUnlimited","Value":"0"}],"SectionId":2},{"Properties":[{"Key":"StartDate","Value":"1 februari 2023"},{"Key":"NumberOfRemainingDays","Value":"16"}],"SectionId":3},{"Properties":[{"Key":"UsedAmount","Value":"0.00"}],"SectionId":4}]}
        header = {"Content-Type": "application/json"}
        response = self.s.get("https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo",data='{"Msisdn": "'+self.msisdn+'"}',headers=header,timeout=10)
        _LOGGER.debug("youfone.be  result status code: " + str(response.status_code))
        _LOGGER.debug("youfone.be  result " + response.text)
        assert response.status_code == 200
        # return next(Telemeter.from_json(response.json()))
        return response.json()
        
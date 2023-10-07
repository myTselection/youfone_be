import logging
import asyncio
from datetime import date, datetime, timedelta
import calendar

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.util import Throttle
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME
)

from . import DOMAIN, NAME
from .utils import *

_LOGGER = logging.getLogger(__name__)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional("country"): cv.string
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)


async def dry_setup(hass, config_entry, async_add_devices):
    config = config_entry
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    country = config.get("country")
    if not country or country == "":
        country = "BE"

    check_settings(config, hass)
    sensors = []
    
    componentData = ComponentData(
        username,
        password,
        country,
        async_get_clientsession(hass),
        hass
    )
    await componentData._forced_update()
    assert componentData._user_details is not None
    assert componentData._usage_details is not None
    assert componentData._msisdn is not None
    
    for msisdn in componentData._msisdn.keys():
        sensorMobile = ComponentMobileSensor(componentData, hass, msisdn)
        # await sensorMobile.async_update()
        sensors.append(sensorMobile)
    
    for msisdn in componentData._msisdn.keys():
        sensorInternet = ComponentInternetSensor(componentData, hass, msisdn)
        # await sensorInternet.async_update()
        sensors.append(sensorInternet)

    for msisdn in componentData._msisdn.keys():
        sensorSubscription = ComponentSubscriptionSensor(componentData, hass, msisdn)
        # await sensorSubscription.async_update()
        sensors.append(sensorSubscription)
    
    async_add_devices(sensors)


async def async_setup_platform(
    hass, config_entry, async_add_devices, discovery_info=None
):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_platform " + NAME)
    await dry_setup(hass, config_entry, async_add_devices)
    return True


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_entry " + NAME)
    config = config_entry.data
    await dry_setup(hass, config, async_add_devices)
    return True


async def async_remove_entry(hass, config_entry):
    _LOGGER.info("async_remove_entry " + NAME)
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass
        

class ComponentData:
    def __init__(self, username, password, country, client, hass):
        self._username = username
        self._password = password
        self._country = country
        self._client = client
        self._session = ComponentSession(self._country)
        self._user_details = None
        self._usage_details = None
        self._subscription_details = None
        self._hass = hass
        self._lastupdate = None
        self._msisdn = None
        
    # same as update, but without throttle to make sure init is always executed
    async def _forced_update(self):
        _LOGGER.info("Fetching init stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession(self._country)

        if self._session:
            self._user_details = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            _LOGGER.info(f"{NAME} init login completed")
            self._msisdn = self._session.msisdn
            _LOGGER.debug(f"{NAME} init login _msisdn = {self._msisdn}")
            self._usage_details = await self._hass.async_add_executor_job(lambda: self._session.usage_details())
            _LOGGER.debug(f"{NAME} init usage_details data: {self._usage_details}")
            self._subscription_details = await self._hass.async_add_executor_job(lambda: self._session.subscription_details())
            _LOGGER.debug(f"{NAME} init subscription_details data: {self._subscription_details}")
            self._lastupdate = datetime.now()
                
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        await self._forced_update()

    async def update(self):
        await self._update()
    
    def clear_session(self):
        self._session : None


    @property
    def unique_id(self):
        return f"{NAME} {self._username}"
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id




class ComponentMobileSensor(Entity):
    def __init__(self, data, hass, phonenumber):
        self._data = data
        self._hass = hass
        self._last_update = None
        self._period_start_date = None
        self._period_left = None
        self._total_volume = None
        self._isunlimited = None
        self._extracosts = None
        self._extracosts_details = None
        self._used_percentage = None
        self._period_used_percentage = None
        self._phonenumber = phonenumber
        self._includedvolume_usage = None
        self._country = self._data._country

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._used_percentage

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        # self._phonenumber = self._data._user_details.get('Object').get('Customers')[0].get('Msisdn')
        self._country = self._data._country
        self._period_start_date = self._data._usage_details[self._phonenumber].get('Object')[2].get('Properties')[0].get('Value')
        self._period_left = int(self._data._usage_details[self._phonenumber].get('Object')[2].get('Properties')[1].get('Value'))
        # date_string = self._period_start_date
        # month_name = date_string.split()[1]
        # month_name = languages.get(name=month_name).name
        # date_string = date_string.replace(month_name, "February")
        # date_object = parser.parse(date_string)
        # period_length = calendar.monthrange(date_object.year, date_object.month)[1]
        # today = datetime.today()
        # period_length = calendar.monthrange(today.year, today.month)[1]
        
        now = datetime.now()
        first_day_of_month = datetime(now.year, now.month, 1)
        # Get the total number of days in the current month
        days_in_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1)).day

        # Get the number of days completed so far as a fraction of days
        total_seconds_in_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - first_day_of_month).total_seconds()
        seconds_completed = (now - first_day_of_month).total_seconds()
        days_completed = seconds_completed / total_seconds_in_month
        self._period_used_percentage = round(100 * days_completed,1)
        
        
        self._isunlimited = self._data._usage_details[self._phonenumber].get('Object')[1].get('Properties')[3].get('Value')
        self._includedvolume_usage = self._data._usage_details[self._phonenumber].get('Object')[1].get('Properties')[0].get('Value')
        self._total_volume = self._data._usage_details[self._phonenumber].get('Object')[1].get('Properties')[1].get('Value')
        if self._isunlimited == '1':
            self._used_percentage = self._data._usage_details[self._phonenumber].get('Object')[1].get('Properties')[2].get('Value')
        else:
            self._used_percentage = round((int(self._includedvolume_usage)/int(self._total_volume.split(" ")[0]))*100,2)
        try:
            self._extracosts = self._data._usage_details[self._phonenumber].get('Object')[3].get('Properties')[0].get('Value')
        except IndexError: 
            self._extracosts = 0
        if self._extracosts != 0:
            self._extracosts_details = ", ".join(f"€{obj['Costs']} ({obj['Description']} - {obj['UsedAmount']})" for obj in self._data._usage_details[self._phonenumber].get('extra').get('Object'))
            
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:phone-plus"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} {self._phonenumber} voice sms"
        )

    @property
    def name(self) -> str:
        return f"{self._phonenumber} voice sms"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "phone_number": self._phonenumber,
            "used_percentage": self._used_percentage,
            "period_used_percentage": self._period_used_percentage,
            "total_volume": self._total_volume,
            "includedvolume_usage": self._includedvolume_usage,
            "unlimited": self._isunlimited,
            "period_start": self._period_start_date,
            "period_days_left": self._period_left,
            "extra_costs": self._extracosts,
            "extra_costs_details": self._extracosts_details,
            "user_details_json": self._data._user_details,
            "usage_details_json": self._data._usage_details[self._phonenumber],
            "subscription_details_json": self._data._subscription_details[self._phonenumber],
            "country": self._country
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"

    @property
    def friendly_name(self) -> str:
        return self.unique_id
        

class ComponentInternetSensor(Entity):
    def __init__(self, data, hass, phonenumber):
        self._data = data
        self._hass = hass
        self._phonenumber = phonenumber
        self._last_update = None
        self._period_start_date = None
        self._period_left = None
        self._total_volume = None
        self._isunlimited = None
        self._extracosts = None
        self._extracosts_details = None
        self._period_used_percentage = None
        self._used_percentage = None
        self._includedvolume_usage = None
        self._country = self._data._country

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._used_percentage

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        self._phonenumber = self._phonenumber
        self._country = self._data._country
        
        self._period_start_date = self._data._usage_details[self._phonenumber].get('Object')[2].get('Properties')[0].get('Value')
        self._period_left = int(self._data._usage_details[self._phonenumber].get('Object')[2].get('Properties')[1].get('Value'))
        now = datetime.now()
        first_day_of_month = datetime(now.year, now.month, 1)
        # Get the total number of days in the current month
        days_in_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1)).day

        # Get the number of days completed so far as a fraction of days
        total_seconds_in_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - first_day_of_month).total_seconds()
        seconds_completed = (now - first_day_of_month).total_seconds()
        days_completed = seconds_completed / total_seconds_in_month
        self._period_used_percentage = round(100 * days_completed,1)
        
        self._total_volume = self._data._usage_details[self._phonenumber].get('Object')[0].get('Properties')[1].get('Value')
        self._isunlimited = self._data._usage_details[self._phonenumber].get('Object')[0].get('Properties')[3].get('Value')
        self._includedvolume_usage = self._data._usage_details[self._phonenumber].get('Object')[0].get('Properties')[0].get('Value')
        if self._isunlimited == '1':
            self._used_percentage = self._data._usage_details[self._phonenumber].get('Object')[0].get('Properties')[2].get('Value')
        else:
            self._used_percentage = round((int(self._includedvolume_usage)/int(self._total_volume.split(" ")[0]))*100,2)
        try:
            self._extracosts = self._data._usage_details[self._phonenumber].get('Object')[3].get('Properties')[0].get('Value')
        except IndexError: 
            self._extracosts = 0
        if self._extracosts != 0:
            self._extracosts_details = ", ".join(f"€{obj['Costs']} ({obj['Description']} - {obj['UsedAmount']})" for obj in self._data._usage_details[self._phonenumber].get('extra').get('Object'))
            
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:web"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} {self._phonenumber} internet"
        )

    @property
    def name(self) -> str:
        return f"{self._phonenumber} internet"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "phone_number": self._phonenumber,
            "used_percentage": self._used_percentage,
            "period_used_percentage": self._period_used_percentage,
            "total_volume": self._total_volume,
            "includedvolume_usage": self._includedvolume_usage,
            "unlimited": self._isunlimited,
            "period_start": self._period_start_date,
            "period_days_left": self._period_left,
            "extra_costs": self._extracosts,
            "extra_costs_details": self._extracosts_details,
            "usage_details_json": self._data._usage_details[self._phonenumber],
            "subscription_details_json": self._data._subscription_details[self._phonenumber],
            "country": self._country
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )


    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"

    @property
    def friendly_name(self) -> str:
        return self.unique_id
        
class ComponentSubscriptionSensor(Entity):
    def __init__(self, data, hass, phonenumber):
        self._data = data
        self._hass = hass
        self._last_update = None
        self._phonenumber = phonenumber
        # Section 21
        self._SubscriptionType = None
        self._Price = None
        self._ContractStartDate = None
        self._ContractDuration = None
        # Section 23
        self._Msisdn = self._data._subscription_details[self._phonenumber][23]['Msisdn']
        self._PUK = None
        self._ICCShort = None
        self._MsisdnStatus = None
        # Section 24
        self._DataSubscription = None
        # Section 26
        self._VoiceSmsSubscription = None
        self._country = self._data._country

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._SubscriptionType

    async def async_update(self):
        await self._data.update()
        subscription_details       = self._data._subscription_details[self._phonenumber]

        self._last_update          =  self._data._lastupdate;
        # Section 21
        self._SubscriptionType     = subscription_details[21]['AbonnementType'].replace("<br/>"," - ")
        self._Price                = subscription_details[21]['Price']
        self._ContractStartDate    = subscription_details[21]['ContractStartDate']
        self._ContractDuration     = subscription_details[21]['ContractDuration']
        # Section 23
        self._Msisdn               = subscription_details[23]['Msisdn']
        self._PUK                  = subscription_details[23]['PUK']
        self._ICCShort             = subscription_details[23]['ICCShort']
        self._MsisdnStatus         = subscription_details[23]['MsisdnStatus']
        # Section 24
        self._DataSubscription     = subscription_details[24]['DataSubscription']
        # Section 26
        self._VoiceSmsSubscription = subscription_details[26]['VoiceSmsSubscription']
        self._country = self._data._country
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:account-cog"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} {self._Msisdn} subscription info"
        )

    @property
    def name(self) -> str:
        return f"{self._Msisdn} subscription info"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "SubscriptionType": self._SubscriptionType,
            "Price": self._Price,
            "ContractStartDate": self._ContractStartDate,
            "ContractDuration": self._ContractDuration,
            "Msisdn": self._Msisdn,
            "PUK": self._PUK,
            "ICCShort": self._ICCShort,
            "MsisdnStatus": self._MsisdnStatus,
            "DataSubscription": self._DataSubscription,
            "VoiceSmsSubscription": self._VoiceSmsSubscription,
            "country": self._country,
            "user_details_json": self._data._user_details,
            "usage_details_json": self._data._usage_details[self._phonenumber],
            "subscritpion_details_json": self._data._subscription_details[self._phonenumber]
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )


    @property
    def unit(self) -> str:
        """Unit"""
        return str

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "string"

    @property
    def friendly_name(self) -> str:
        return self.unique_id

#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
import httpx
import os

# phonenumbers library required
import phonenumbers

from classes.Profile import Profile
from classes.account.Account import Account
from tools.Tool import Tool

from classes.account.WebsiteAccount import WebsiteAccount
from classes.types.OpsePhoneNumber import OpsePhoneNumber
from classes.types.OpseStr import OpseStr

from ignorant.core import *

from utils.DataTypeInput import DataTypeInput
from utils.DataTypeOutput import DataTypeOutput
from utils.utils import print_debug, print_error, print_warning


class IgnorantTool(Tool):
    """
    Class which describe an IgnorantTool
    """
    """
    This code is inspired by: 
    https://github.com/megadose/ignorant
    """
    deprecated = False

    modules = import_submodules("ignorant.modules")
    websites = get_functions(modules)

    def __init__(self):
        super().__init__()

    @staticmethod
    def get_config() -> dict[str]:
        return {
            'active': True,
            'deprecated': False
        }

    @staticmethod
    def get_lst_input_data_types() -> dict[str, bool]:
        return {
            DataTypeInput.PHONE_NUMBER: True, # Required data
        }

    @staticmethod
    def get_lst_output_data_types() -> list[str]:
        return [
            DataTypeOutput.ACCOUNT,
        ]

    def execute(self):
        phoneNumbers: list[OpseStr] = self.get_default_profile().get_lst_phone_numbers()
        profile: Profile = self.get_default_profile().clone()

        for phoneNumber in phoneNumbers:
            print_debug("Investigating " + str(phoneNumber) + " ...")
            try:
                accounts = self.list_website_accounts(phoneNumber, profile)
                profile.set_lst_accounts(accounts)
            except Exception as e:
                print_error(" " + str(e), True)
                print_warning(" Profiles produced by Ignorant might be incompleted due to an error")
        
        self.append_profile(profile)

    def list_website_accounts(self, phoneNumber, profile: Profile = None) -> list[Account]:
        if profile == None:
            profile = Profile(lst_phone_numbers=[phoneNumber], lst_accounts=[])

        results = []

        asyncio.run(self.ignoranttool_callback(phoneNumber, results))

        accounts = []
        for result in results:
            print(result)
            try:
                if 'exists' in result.keys() and result.get('exists'):
                    #print_debug(phoneNumber + " is register on " + result.get('name'))
                    account = WebsiteAccount(
                        website_name = result.get('name'),
                        website_url = result.get('domain'),
                        phone_number = phoneNumber
                    )
                    accounts.append(account)
            except Exception as e:
                print_error(" [Ignorant:ignorant_call:" + result.get('name') + "] " + str(e), True)

        # Add found accounts to the profile
        return accounts

    async def ignorant_module_callback(self, module, phoneNumber: str, client, module_result) -> None:
        """ """
        try:
            # Process phone number here, directly before launching 
            parsedPhoneNumber = phonenumbers.parse(str(phoneNumber), None)

            countryID = parsedPhoneNumber.country_code
            nationalID = parsedPhoneNumber.national_number

            await launch_module(module, nationalID, countryID, client, module_result)
        except Exception as e:
            print_warning(" " + str(module) + " has stopped during execution : " + str(e), True)


    async def ignoranttool_callback(self, phoneNumber: str, module_result) -> None:
        """ """
        async with httpx.AsyncClient() as client:
            ret = await asyncio.gather(*[self.ignorant_module_callback(module, phoneNumber, client, module_result) for module in IgnorantTool.websites])
        print_debug("Finalized all. Return is a list of len {} outputs.".format(len(ret)))

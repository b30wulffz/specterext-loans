import logging

from cryptoadvance.specter.services.service import Service, devstatus_alpha, devstatus_prod, devstatus_beta
from cryptoadvance.specter.managers.genericdata_manager import GenericDataManager
# A SpecterError can be raised and will be shown to the user as a red banner
from cryptoadvance.specter.specter_error import SpecterError
from flask import current_app as app
from cryptoadvance.specter.wallet import Wallet
from flask_apscheduler import APScheduler

import json
from pathlib import Path

logger = logging.getLogger(__name__)

class CurrentServiceStorageManager(GenericDataManager):
    name_of_json_file = "common_service_storage.json"

    def update_common_service_data(self, service_id, value):
        self.data = {
            service_id: value   
        }  
        self._save()

    def get_common_service_data(self, service_id):
        if service_id not in self.data:
            self.data[service_id] = {}
        return self.data[service_id]

class LoansService(Service):
    id = "loans"
    name = "Loans Service"
    icon = "loans/img/ghost.png"
    logo = "loans/img/logo.png"
    desc = "Where a loans grows bigger."
    has_blueprint = True
    blueprint_module = "b30wulffz.specterext.loans.controller"
    devstatus = devstatus_alpha
    isolated_client = False
    currentServiceStorage = CurrentServiceStorageManager(Path('{}/.specter_dev/'.format(Path.home())))

    # TODO: As more Services are integrated, we'll want more robust categorization and sorting logic
    sort_priority = 2

    # ServiceEncryptedStorage field names for this service
    # Those will end up as keys in a json-file
    SPECTER_WALLET_ALIAS = "wallet"

    def callback_after_serverpy_init_app(self, scheduler: APScheduler):

        # custom struct for data storage
        common_data = self.get_common_service_data()
                
        if "ecash_addresses" not in common_data:
            common_data["ecash_addresses"] = {}
        if "incoming_requests" not in common_data:
            common_data["incoming_requests"] = []
        if "active_loans" not in common_data:
            common_data["active_loans"] = []
        if "inactive_loans" not in common_data:
            common_data["inactive_loans"] = []
        if "return_btc" not in common_data:
            common_data["return_btc"] = {}
        if "deduct_btc" not in common_data:
            common_data["deduct_btc"] = 0
        if "return_ecash" not in common_data:
            common_data["return_ecash"] = 0

        self.update_common_service_data(common_data)
    
        # def every5seconds(hello, world="world"):
        #     with scheduler.app.app_context():
        #         print(f"Called {hello} {world} every5seconds")
        # Here you can schedule regular jobs. triggers can be one of "interval", "date" or "cron"
        # Examples:
        # interval: https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html
        # scheduler.add_job("every5seconds4", every5seconds, trigger='interval', seconds=5, args=["hello"])
        
        # Date: https://apscheduler.readthedocs.io/en/3.x/modules/triggers/date.html
        # scheduler.add_job("MyId", my_job, trigger='date', run_date=date(2009, 11, 6), args=['text'])
        
        # cron: https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html
        # sched.add_job("anotherID", job_function, trigger='cron', day_of_week='mon-fri', hour=5, minute=30, end_date='2014-05-30')
        
        # Maybe you should store the scheduler for later use:
        self.scheduler = scheduler
        
    # There might be other callbacks you're interested in. Check the callbacks.py in the specter-desktop source.
    # if you are, create a method here which is "callback_" + callback_id

    @classmethod
    def get_associated_wallet(cls) -> Wallet:
        """Get the Specter `Wallet` that is currently associated with this service"""
        service_data = cls.get_current_user_service_data()
        if not service_data or cls.SPECTER_WALLET_ALIAS not in service_data:
            # Service is not initialized; nothing to do
            return
        try:
            return app.specter.wallet_manager.get_by_alias(
                service_data[cls.SPECTER_WALLET_ALIAS]
            )
        except SpecterError as e:
            logger.debug(e)
            # Referenced an unknown wallet
            # TODO: keep ignoring or remove the unknown wallet from service_data?
            return

    @classmethod
    def set_associated_wallet(cls, wallet: Wallet):
        """Set the Specter `Wallet` that is currently associated with this Service"""
        cls.update_current_user_service_data({cls.SPECTER_WALLET_ALIAS: wallet.alias})
        
    @classmethod
    def update_common_service_data(cls, value):
        cls.currentServiceStorage.update_common_service_data(cls.id, value)

    @classmethod
    def get_common_service_data(cls):
        return cls.currentServiceStorage.get_common_service_data(cls.id)

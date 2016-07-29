"""Module for creating an application in spinnaker.

Looks to see if the application exists, and if not creates the application.
"""
import logging
from pprint import pformat

import requests

from ..consts import API_URL, HEADERS
from ..utils import get_template, check_task, post_task


class SpinnakerApp:
    """Class to manage and create Spinnaker applications

    Args:
        app (str): Application name.
        email (str): Email associated with application.
        project (str): Git namespace or project group
        repo (str): Repository name

    Attributes:
        appinfo (dict): A dictionary containing the provided arguments
        appname (str): The name of the application.
    """

    def __init__(self, app=None, email=None, project=None, repo=None):
        self.log = logging.getLogger(__name__)

        self.appinfo = {'app': app,
                        'email': email,
                        'project': project,
                        'repo': repo}
        self.appname = app

    def get_accounts(self, provider='aws'):
        """Get Accounts added to Spinnaker.

        Args:
            provider (str): What provider to find accounts for.

        Returns:
            list: list of dicts of Spinnaker credentials matching _provider_.

        Raises:
            AssertionError: Failure getting accounts from Spinnaker.
        """
        url = '{gate}/credentials'.format(gate=API_URL)
        response = requests.get(url)

        assert response.ok, 'Failed to get accounts: {0}'.format(response.text)

        all_accounts = response.json()
        filtered_accounts = []
        for account in all_accounts:
            if account['type'] == provider:
                filtered_accounts.append(account)

        return filtered_accounts

    def create_app(self):
        """Send a POST to spinnaker to create a new application with class variables.

        Raises:
            AssertionError: Application creation failed.
        """
        self.appinfo['accounts'] = self.get_accounts()
        self.log.debug('App info:\n%s', pformat(self.appinfo))

        jsondata = get_template(template_file='app_data_template.json',
                                appinfo=self.appinfo)

        taskid = post_task(jsondata)
        check_task(taskid)

        self.log.info("Successfully created %s application", self.appname)
        return

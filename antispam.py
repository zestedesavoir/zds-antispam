# We need to be in the script's directory
import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))

from training import vectorizer, clf
from send_alerts import send_alerts

from datetime import datetime
import json
import logging
import requests
import sys
from time import sleep

# The structure of this bot is inspired from tleb's zds-user-map at https://github.com/tleb/zds-user-map

class Antispam:

    URI_BASE = 'https://zestedesavoir.com'
    URI_TOKEN = '/oauth2/token/'
    URI_LIST_USERS = '/api/membres/?page_size={}'
    URI_USER = '/api/membres/{}/'
    URI_SEND = '/api/mps/{}/messages/'

    secrets_file = 'secrets.json'
    secrets = {}

    tokens_file = 'tokens.json'
    tokens = {}

    reported_users_file = 'reported_users.txt'
    reported_users = []

    def __init__(self, page_size=50):
        self.page_size = page_size

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.FileHandler('antispam.log', mode='a'))
        self.logger.info('\n\n# Antispam started ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n\n')

        self.load_secrets()
        self.load_tokens()
        self.load_reported_users()

        self.runtime()

    def runtime(self):
        if self.tokens.get('access_token') is None:
            self.refresh_tokens()

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.tokens['access_token']
        }

        self.logger.debug('GET ' + self.URI_LIST_USERS.format(self.page_size))
        response = requests.get(self.URI_BASE + self.URI_LIST_USERS.format(self.page_size), headers=headers)
        if response.status_code in (401, 429):
            self.logger.warning('HTTP Error 401 or 429, need to refresh tokens')
            self.tokens['access_token'] = None
            return self.runtime()
        response.raise_for_status()
        members = response.json()['results']

        users_to_report = []
        for member in members:
            if member['username'] in self.reported_users:
                self.logger.info('✘  %s has already been reported as potential spam' % member['username'])
                continue

            # Avoiding too many requests in a short time
            sleep(1)

            self.logger.debug('GET ' + self.URI_USER.format(member['id']))
            response = requests.get(self.URI_BASE + self.URI_USER.format(member['id']), headers=headers)
            if response.status_code in (401, 429):
                self.logger.warning('HTTP Error 401 or 429, need to refresh tokens')
                self.tokens['access_token'] = None
                return self.runtime()
            response.raise_for_status()
            biography = response.json()['biography']

            if biography == '':
                self.logger.info('∅  %s has no biography' % member['username'])
                continue

            if self.check(biography) == 0:
                self.logger.info("✘  %s's biography looks like spam" % member['username'])
                users_to_report.append(member['username'])
            else:
                self.logger.info("✔️  %s's biography doesn't look like spam" % member['username'])

        if users_to_report:
            try:
                send_alerts(
                    website=self.URI_BASE,
                    bot_username=self.secrets['username'],
                    bot_password=self.secrets['password'],
                    suspected_usernames=users_to_report
                )

                self.logger.info('\n=> Alert sent!')
            except requests.exceptions.HTTPError as e:
                self.logger.exception(e)

                message = "Ces membres sont potentiellement des spammeurs :\n"

                for user in users_to_report:
                    message = message + '\n- @**' + user + '**'

                body = {
                    'text': message
                }
                self.logger.debug('POST ' + self.URI_SEND.format(self.secrets['topic_id']))
                response = requests.post(self.URI_BASE + self.URI_SEND.format(self.secrets['topic_id']), json=body, headers=headers)
                if response.status_code in (401, 429):
                    self.logger.warning('HTTP Error 401 or 429, need to refresh tokens')
                    self.tokens['access_token'] = None
                    return self.runtime()
                response.raise_for_status()

                self.logger.info('\n=> Message sent!')

            self.reported_users += users_to_report
            self.save_reported_users()

    def check(self, biography):
        X_new_tfidf = vectorizer.transform([biography])
        return clf.predict(X_new_tfidf)[0]

    def refresh_tokens(self):
        if self.tokens.get('refresh_token') is None:
            self.refresh_tokens_from_logins()

        body = {
            'grant_type': 'refresh_token',
            'client_id': self.secrets['client_id'],
            'client_secret': self.secrets['client_secret'],
            'refresh_token': self.tokens['refresh_token'],
        }

        self.logger.debug('POST ' + self.URI_TOKEN)
        response = requests.post(self.URI_BASE + self.URI_TOKEN, json=body)
        response.raise_for_status()
        content = response.json()

        self.tokens = {
            'access_token': content['access_token'],
            'refresh_token': content['refresh_token']
        }
        self.save_tokens()

    def refresh_tokens_from_logins(self):
        body = {
            'grant_type': 'password',
            'client_id': self.secrets['client_id'],
            'client_secret': self.secrets['client_secret'],
            'username': self.secrets['username'],
            'password': self.secrets['password'],
        }

        self.logger.debug('POST ' + self.URI_TOKEN)
        response = requests.post(self.URI_BASE + self.URI_TOKEN, json=body)
        response.raise_for_status()
        content = response.json()

        self.tokens = {
            'access_token': content['access_token'],
            'refresh_token': content['refresh_token']
        }
        self.save_tokens()

    def save_tokens(self):
        with open(self.tokens_file, 'w') as f:
            json.dump(self.tokens, f)

    def load_tokens(self):
        try:
            with open(self.tokens_file, 'r') as f:
                self.tokens = json.load(f)
        except FileNotFoundError:
            self.refresh_tokens()

    def load_secrets(self):
        with open(self.secrets_file, 'r') as f:
            self.secrets = json.load(f)

    def save_reported_users(self):
        with open(self.reported_users_file, 'w') as f:
            f.write('\n'.join(self.reported_users))

    def load_reported_users(self):
        try:
            with open(self.reported_users_file, 'r') as f:
                self.reported_users = f.read().split('\n')
        except FileNotFoundError:
            self.reported_users = []

if len(sys.argv) > 1:
    page_size = int(sys.argv[1])
    Antispam(page_size)

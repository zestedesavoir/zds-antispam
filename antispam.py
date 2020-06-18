# We need to be in the script's directory
import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))

from training import count_vect, tfidf_transformer, clf

from datetime import datetime
import json
import logging
import requests
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
    
    last_user_file = 'last_user.txt'
    last_user = ''

    page_size = 50

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.FileHandler('antispam.log', mode='w'))
        self.logger.info('\n\n# Antispam started ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n\n')
        self.logger.addHandler(logging.StreamHandler())

        self._load_secrets()
        self._load_tokens()
        self._load_last_user()

        self.runtime()

    def runtime(self):
        if self.tokens.get('access_token') is None:
            self._refresh_tokens()

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.tokens['access_token']
        }

        self.logger.debug('GET ' + self.URI_LIST_USERS.format(self.page_size))
        response = requests.get(self.URI_BASE + self.URI_LIST_USERS.format(self.page_size), headers=headers)
        if response.status_code in (401, 429):
            self.logger.warn('HTTP Error 401 or 429, need to refresh tokens')
            self.tokens['access_token'] = None
            return self.runtime()
        response.raise_for_status()
        members = response.json()['results']

        potential_spammers = []
        for member in members:
            if self.last_user == str(member['id']):
                break

            # Avoiding too many requests in a short time
            sleep(1)

            self.logger.debug('GET ' + self.URI_USER.format(member['id']))
            response = requests.get(self.URI_BASE + self.URI_USER.format(member['id']), headers=headers)
            if response.status_code in (401, 429):
                self.logger.warn('HTTP Error 401 or 429, need to refresh tokens')
                self.tokens['access_token'] = None
                return self.runtime()
            response.raise_for_status()
            biography = response.json()['biography']

            if biography == '':
                self.logger.info('∅  %s has no biography' % member['username'])
                continue

            if self.check(biography) == 0:
                self.logger.info("✘  %s's biography looks like spam" % member['username'])
                potential_spammers.append(member['username'])
            else:
                self.logger.info("✔️  %s's biography doesn't look like spam" % member['username'])

        if potential_spammers:
            message = "Those members are potential spammers:\n"

            for spammer in potential_spammers:
                message = message + '\n- @**' + spammer + '**'

            body = {
                'text': message
            }
            self.logger.debug('POST ' + self.URI_SEND.format(self.secrets['topic_id']))
            response = requests.post(self.URI_BASE + self.URI_SEND.format(self.secrets['topic_id']), json=body, headers=headers)
            if response.status_code in (401, 429):
                self.logger.warn('HTTP Error 401 or 429, need to refresh tokens')
                self.tokens['access_token'] = None
                return self.runtime()
            response.raise_for_status()
            self.logger.info('\n=> Message sent!')

        self.last_user = str(members[0]['id'])
        self._save_last_user()

    def check(self, biography):
        X_new_counts = count_vect.transform([biography])
        X_new_tfidf = tfidf_transformer.transform(X_new_counts)
        return clf.predict(X_new_tfidf)[0]

    def _refresh_tokens(self):
        if self.tokens.get('refresh_token') is None:
            self._refresh_tokens_from_logins()

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
        self._save_tokens()

    def _refresh_tokens_from_logins(self):
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
        self._save_tokens()

    def _save_tokens(self):
        with open(self.tokens_file, 'w') as f:
            json.dump(self.tokens, f)

    def _load_tokens(self):
        try:
            with open(self.tokens_file, 'r') as f:
                self.tokens = json.load(f)
        except FileNotFoundError:
            self._refresh_tokens()

    def _load_secrets(self):
        with open(self.secrets_file, 'r') as f:
            self.secrets = json.load(f)

    def _save_last_user(self):
        with open(self.last_user_file, 'w') as f:
            f.write(self.last_user)

    def _load_last_user(self):
        try:
            with open(self.last_user_file, 'r') as f:
                self.last_user = f.read()
        except FileNotFoundError:
            self.last_user = ''

Antispam()

# Antispam for Zeste de Savoir

The goal of this project is to detect spam in the biography of Zeste de Savoir member accounts. We have frequently a lot of fake member accounts created only to promote online website with paid services in their biography, it would be nice if those could be flagged automatically as potential spam.

This antispam is a machine learning algorithm trained with data from the actual database of Zeste de Savoir. A bot retrieve the last member accounts and process their biography through the antispam. If the bot thinks the biography is a spam, it sends a private message to alert the moderators.

## Getting training data

We need to open Django's shell with `/opt/zds/wrapper shell` and import those objects:

```py
from django.db.models import Q, F
from zds.member.models import Profile
import json
```

Then, we want for each user to save their username, their biography and the flag indicating if they are banned or not:

```py
raw_data = list(Profile.objects.values('biography', 'can_read', username=F('user__username')))
```

Most biographies are empty, so we remove the users if it's the case:

```py
data = []
for elem in raw_data:
    if elem['biography'] != "":
        data.append(elem)
```

After that, we write the data into a JSON file placed in the webroot so we can access it at the relative URL `/static/antispam-data.json`:

```py
with open('/opt/zds/webroot/static/antispam-data.json', 'w') as f:
    json.dump(data, f)
```

Finally, we retrieve the file and do not forget to remove it with `sudo rm /opt/zds/webroot/static/antispam-data.json`!

In the end, we have `antispam-data.json` with a list of objects with `username`, `biography` and `can_read`.

## Installing the dependencies

We need to create a virtual environment, activate it and install the dependencies:

```py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the antispam

We need to put the secrets in a JSON file nammed `secrets.json` with this structure:

```json
{
    "client_id": "foo",
    "client_secret": "bar",
    "username": "something",
    "password": "else",
    "topic_id": "42"
}
```

Then, we just have to run `antispam.py`!

It can be automated using a cronjob because it keeps track of already reported potential spammers in a text file nammed `reported_users.txt`.

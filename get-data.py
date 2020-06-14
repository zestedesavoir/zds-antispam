# This file needs to be runned on the server with `/opt/zds/wrapper shell`
# With this file, we get all the data we need from the database

from django.db.models import Q, F
from zds.member.models import Profile
import json

# For each user, we save their username and if they are banned or not
# We also keep their biography, signature and website
raw_data = list(Profile.objects.values('biography', 'can_read', username=F('user__username')))

# We remove users when their biography, signature and website are empty
data = []
for elem in raw_data:
    if elem['biography'] != "":
        data.append(elem)

# We write the file so it can be accessed on our website at https://zestedesavoir.com/static/antispam-data.json
with open('/opt/zds/webroot/static/antispam-data.json', 'w') as f:
    json.dump(data, f)

# Do not forget to remove the file with `sudo rm /opt/zds/webroot/static/antispam-data.json`!

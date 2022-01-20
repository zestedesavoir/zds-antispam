from bs4 import BeautifulSoup

import requests

def send_alerts(website, bot_username, bot_password, suspected_usernames):
    login_page_url = "/membres/connexion/"
    login_form_url = "/membres/connexion/?next=/"
    login_form_data = {
        "username": bot_username,
        "password": bot_password,
    }

    profile_page_url = "/@"
    profile_form_id = "report-profile"
    profile_form_data = {
        "reason": "Spam potentiel"
    }

    s = requests.session()

    # Bot login

    login_page_req = s.get(website+login_page_url)
    login_page_req.raise_for_status()
    referer = login_page_req.url

    login_page_soup = BeautifulSoup(login_page_req.content, "lxml")
    login_form = login_page_soup.find("form", action=login_form_url)

    for el in login_form.find_all(name=True):
        if "name" in el.attrs:
            if not el.attrs.get("name") in login_form_data:
                login_form_data[el.attrs.get("name")] = el.attrs.get("value")

    s.headers.update({"referer": referer})
    login_auth_req = s.post(website+login_form_url, data=login_form_data)
    login_auth_req.raise_for_status()
    referer = login_auth_req.url

    # Sending alerts

    for username in suspected_usernames:
        s.headers.update({"referer": referer})
        profile_page_req = s.get(website+profile_page_url+username)
        profile_page_req.raise_for_status()
        referer = profile_page_req.url

        profile_page_soup = BeautifulSoup(profile_page_req.content, "lxml")
        profile_form = profile_page_soup.find("form", id=profile_form_id)

        profile_form_url = profile_form.attrs.get("action")

        for el in profile_form.find_all(name=True):
            if "name" in el.attrs:
                if not el.attrs.get("name") in profile_form_data:
                    profile_form_data[el.attrs.get("name")] = el.attrs.get("value")

        s.headers.update({"referer": referer})
        profile_alert_req = s.post(website+profile_form_url, data=profile_form_data)
        profile_alert_req.raise_for_status()
        referer = profile_alert_req.url


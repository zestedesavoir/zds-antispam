# Antispam for Zeste de Savoir

The goal of this project is to detect spam in the biography of Zeste de Savoir member accounts. We have frequently a lot of fake member accounts created only to promote online website with paid services in their biography, it would be nice if those could be flagged automatically as potential spam.

This antispam is a machine learning algorithm trained with data from the actual database of Zeste de Savoir. A bot retrieve the last member accounts and process their biography through the antispam.

## Getting training data

All we need to do is run the `get-data.py` script on the server as the comments in it indicates. In the end, you should have a file nammed `antispam-data.json` with a list of objects with `username`, `biography` and `can_read`.

## Running the antispam

Create a file nammed `secrets.json` with :

```json
{
    "client_id": "foo",
    "client_secret": "bar",
    "username": "something",
    "password": "else",
    "topic_id": "42"
}
```

modify `topic_id` value in `antispam.py` and just run it!

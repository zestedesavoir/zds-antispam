from training import count_vect, tfidf_transformer, clf
import requests


def antispam(biography):
    X_new_counts = count_vect.transform([biography])
    X_new_tfidf = tfidf_transformer.transform(X_new_counts)
    return clf.predict(X_new_tfidf)[0]

page_size = 10
headers = {'Accept': 'application/json'}
response = requests.get('https://zestedesavoir.com/api/membres/?page_size={}'.format(page_size), headers=headers)
response.raise_for_status()
members = response.json()['results']

for member in members:
    response = requests.get('https://zestedesavoir.com/api/membres/{}/'.format(member['id']), headers=headers)
    response.raise_for_status()
        
    biography = response.json()['biography']
    if biography == '':
        print('∅  %s has no biography' % member['username'])
        continue

    if antispam(biography) == '0':
        print("✘  %s's biography looks like spam" % member['username'])
    else:
        print("✔️  %s's biography doesn't look like spam" % member['username'])

if __name__ == '__main__':
    while True:
        inpt = input('Enter a sentence (q to quit): ')

        if inpt == "q":
            break

        print(antispam(inpt), '\n')

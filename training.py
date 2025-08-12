from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from pprint import pprint
import json

# Data importation

_bio = []
_can_read = []

with open('antispam-data.json', 'r') as f:
    _data = json.load(f)

for _elem in _data:
    if not _elem['biography']:
        continue

    _bio.append(_elem['biography'])
    _can_read.append(1 if _elem['can_read'] else 0)

bio_train, bio_test, can_read_train, can_read_test = train_test_split(
    _bio,
    _can_read,
    test_size=0.2,
    random_state=42,
    stratify=_can_read,
)

# Transformation text->number (text preprocessing, tokenizing and filtering of stopwords) and frequency calculation

vectorizer = TfidfVectorizer(lowercase=True, strip_accents="unicode")
bio_train_transformed = vectorizer.fit_transform(bio_train)

# Classifier training

model = LinearSVC(max_iter=5000, loss='hinge', dual="auto")
model.fit(bio_train_transformed, can_read_train)

# Prediction of test data

bio_test_transformed = vectorizer.transform(bio_test)
predicted = model.predict(bio_test_transformed)

if __name__ == '__main__':
    average = 0
    confusions = {}
    for real, pred in zip(can_read_test, predicted):
        if real==pred:
            average += 1

        elem = 'real {} => pred {}'.format(real, pred)

        if not confusions.get(elem, False):
            confusions[elem] = [0, '']

        confusions[elem][0] += 1

    for elem in confusions:
        confusions[elem][1] = '{} %'.format(round(confusions[elem][0]/len(can_read_test)*100))

    print('\n', round(average/len(can_read_test)*100,2), '%\n\n')

    pprint(confusions)


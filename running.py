from training import count_vect, tfidf_transformer, clf

if __name__ == '__main__':
    while True:
        inpt = input('Enter a sentence (q to quit): ')

        if inpt == "q":
            break

        X_new_counts = count_vect.transform([inpt])
        X_new_tfidf = tfidf_transformer.transform(X_new_counts)

        print(clf.predict(X_new_tfidf)[0], '\n')

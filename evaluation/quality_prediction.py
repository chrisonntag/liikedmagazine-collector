import pandas as pd
import numpy as np
import re
import os
import pickle
import joblib
import sqlite3
from settings import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.gaussian_process.kernels import RBF


CWD = os.path.dirname(os.path.abspath(__file__))


# Average word length
# Take the sum of the length of all the words and divide it by the total length of the tweet
def avgword(sentence):
    words = sentence.split()
    if len(words) > 0:
        return sum(len(word) for word in words)/len(words)
    else:
        return 0.0


class QualityPrediction:

    BASE_MODEL = AdaBoostClassifier()  # GaussianProcessClassifier(1.0 * RBF(1.0))
    MODEL_FILE_NAME = 'quality_classifier_dt.pkl'

    def __init__(self):
        try:
            with open(os.path.join(CWD, QualityPrediction.MODEL_FILE_NAME), 'rb') as f:
                self.model = joblib.load(f)
        except FileNotFoundError:
            self.create()

    @staticmethod
    def prepare_features(data, train=True):
        # Feature Selection
        # Add num of hashtags and caption length
        hashtags = []
        hashtags_num = []
        wordcount = []
        charcount = []
        clean_caption = []
        avgword_length = []

        for caption in data['caption']:
            # find hashtags
            tags = re.findall(settings.hashtag_regex, caption)

            # delete mentions and hashtags
            cc = re.sub(r'(#\w+)', '', caption)
            cc = re.sub(r'@[A-Za-z0-9]+', '', cc)
            cc = cc.strip().lower()
            clean_caption.append(cc)

            # Number of chars and words
            charcount.append(len(cc))
            wordcount.append(len(cc.split()))

            # Avg word length
            avgword_length.append(avgword(cc))

            # hashtags
            hashtags_num.append(len(tags))
            hashtags.append(' '.join(tags))

        data['hashtags'] = hashtags
        data['hashtags_num'] = hashtags_num
        data['wordcount'] = wordcount
        data['charcount'] = charcount
        data['avgword'] = avgword_length
        data['clean_caption'] = clean_caption
        data['clean_caption'] = data['clean_caption'].fillna('')

        num_feature_cols = ['quality', 'mentions', 'like_ratio', 'comment_ratio', 'hashtags_num', 'wordcount', 'charcount', 'avgword', 'follower', 'following', 'posts']

        # Vectorizing Hashtags and Caption
        if train:
            c_vectorizer = TfidfVectorizer(stop_words='english')
            h_vectorizer = TfidfVectorizer(stop_words='english')

            vectorized_caption = c_vectorizer.fit_transform(data['clean_caption'])
            vectorized_hashtags = h_vectorizer.fit_transform(data['hashtags'])

            # Dump vectorizers
            pickle.dump(c_vectorizer, open(os.path.join(CWD, 'c_vectorizer.pkl'), 'wb'))
            pickle.dump(h_vectorizer, open(os.path.join(CWD, 'h_vectorizer.pkl'), 'wb'))
        else:
            # Load TfidfVectorizers
            with open(os.path.join(CWD, 'c_vectorizer.pkl'), 'rb') as f:
                c_vectorizer = pickle.load(f)
            with open(os.path.join(CWD, 'h_vectorizer.pkl'), 'rb') as f:
                h_vectorizer = pickle.load(f)

            vectorized_caption = c_vectorizer.transform(data['clean_caption'])
            vectorized_hashtags = h_vectorizer.transform(data['hashtags'])

        # Training the model
        # Features without quality column
        num_features = data[num_feature_cols].iloc[:, 1:].values
        X = np.hstack((vectorized_caption.todense(), vectorized_hashtags.todense(), num_features))

        return X

    @staticmethod
    def train(clf):
        query = "SELECT mediaobject.caption, mediaobject.comment_ratio, mediaobject.like_ratio, mediaobject.mentions, " \
                "mediaobject.quality, user.follower, user.following, user.posts " \
                "FROM mediaobject " \
                "INNER JOIN user ON mediaobject.user_id=user.user_id " \
                "WHERE mediaobject.quality IS NOT NULL"
        db = sqlite3.connect(settings.database)
        data = pd.read_sql_query(query, db)
        data = data.dropna()

        # The data-set seems unbalanced, therefore down-sample the dataset to the minority class.
        count_low, count_high = data['quality'].value_counts()
        low_quality = data[data['quality'] == 0]
        high_quality = data[data['quality'] == 1]

        low_quality_under = low_quality.sample(count_high)
        data = pd.concat([low_quality_under, high_quality], axis=0)

        X = QualityPrediction.prepare_features(data)
        y = data.quality

        clf.fit(X, y)

        return clf

    def create(self):
        clf = self.train(self.BASE_MODEL)
        pickle.dump(clf, open(os.path.join(CWD, QualityPrediction.MODEL_FILE_NAME), 'wb'))
        self.model = clf

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


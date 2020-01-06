import sqlite3
import pandas as pd
import numpy as np
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF


DB = sqlite3.connect('../labeled_media.db')


# Average word length
# Take the sum of the length of all the words and divide it by the total length of the tweet
def avgword(sentence):
    words = sentence.split()
    if len(words) > 0:
        return sum(len(word) for word in words)/len(words)
    else:
        return 0.0


class QualityPrediction:

    BASE_MODEL = GaussianProcessClassifier(1.0 * RBF(1.0))
    MODEL_FILE = 'quality_model.pkl'
    MODEL = None

    def __init__(self):
        model = self.load()
        if model is not None:
            self.MODEL = model
        else:
            self.MODEL = self.create()

    @staticmethod
    def train(clf):
        query = "SELECT mediaobject.caption, mediaobject.comment_ratio, mediaobject.like_ratio, mediaobject.mentions, " \
                "mediaobject.quality, user.follower, user.following, user.posts " \
                "FROM mediaobject " \
                "INNER JOIN user ON mediaobject.user_id=user.user_id " \
                "WHERE mediaobject.quality IS NOT NULL"
        data = pd.read_sql_query(query, DB)
        data = data.dropna()

        # The dataset seems unbalanced, therefore either down- or upsample the dataset.
        count_low, count_high = data['quality'].value_counts()
        low_quality = data[data['quality'] == 0]
        high_quality = data[data['quality'] == 1]

        low_quality_under = low_quality.sample(count_high)
        data = pd.concat([low_quality_under, high_quality], axis=0)

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
            tags = re.findall(r'(?<=[\s>])#(\d*[A-Za-z_]+\d*)\b(?!;)', caption)

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
        vectorizer = TfidfVectorizer(stop_words='english')

        vectorized_caption = vectorizer.fit_transform(data['clean_caption']).todense()
        vectorized_hashtags = vectorizer.fit_transform(data['hashtags']).todense()

        # Training the model
        # Features without quality column
        num_features = data[num_feature_cols].iloc[:, 1:].values
        X = np.hstack((vectorized_caption, vectorized_hashtags, num_features))
        y = data.quality

        clf.fit(X, y)

        return clf

    def create(self, filename=MODEL_FILE):
        clf = self.train(self.BASE_MODEL)
        joblib.dump(clf, filename)
        return clf

    def load(self, filename=MODEL_FILE):
        try:
            clf = joblib.load(filename)
            return clf
        except Exception:
            return None

    def predict(self, X):
        return self.MODEL.predict(X)


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn import metrics

import warnings
warnings.filterwarnings('ignore')
class Model:
    def __init__(self, ticker):
        pass
        self.ticker = ticker
        self.df = pd.read_csv(f'{ticker}_COMPLETE_DATA/04_Market_Data/Price_History.csv')
        self.df.head()


        
    def show_graph(self):
        plt.figure(figsize=(15,5))
        plt.plot(self.df['Close'])
        plt.title(f'{self.ticker} Close price.', fontsize=15)
        plt.ylabel('Price in dollars.')
        plt.show()
    def plot_close_high(self):
        features = ['Open', 'High', 'Low', 'Close', 'Volume']

        plt.subplots(figsize=(20,10))

        for i, col in enumerate(features):
            plt.subplot(2,3,i+1)
            sb.distplot(self.df[col])
        plt.show()
        plt.subplots(figsize=(20,10))
        for i, col in enumerate(features):
            plt.subplot(2,3,i+1)
            sb.boxplot(self.df[col])
        plt.show()
    def train_model(self):

        # Force the conversion and verify
        self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce', utc=True)

        # Add these debug prints
        print("Date column dtype:", self.df['Date'].dtype)
        print("First few dates:")
        print(self.df['Date'].head())
        print("\nFailed conversions:")
        print(self.df[self.df['Date'].isna()].head())

        # Only extract month if we have datetime values
        if pd.api.types.is_datetime64_any_dtype(self.df['Date']):
            self.df['month'] = self.df['Date'].dt.month
            print("Month extraction successful!")
        else:
            print("ERROR: Date column is not datetime type!")
            print(f"Current type: {self.df['Date'].dtype}")

        # Quarter-end months are multiples of 3
        self.df['is_quarter_end'] = (self.df['month'] % 3 == 0).astype(int)

        # Price-based engineered features
        self.df['open-close'] = self.df['Open'] - self.df['Close']
        self.df['low-high'] = self.df['Low'] - self.df['High']

        # Prediction target (binary up/down)
        self.df['target'] = np.where(
            self.df['Close'].shift(-1) > self.df['Close'], 1, 0
        )

        # Select features
        features = self.df[['open-close', 'low-high', 'is_quarter_end']]
        target = self.df['target']

        # Standardize features
        scaler = StandardScaler()
        features = scaler.fit_transform(features)

        # Train/test split
        X_train, X_valid, Y_train, Y_valid = train_test_split(
            features, target, test_size=0.1, random_state=2022
        )

        print(X_train.shape, X_valid.shape)

        models = [
            LogisticRegression(),
            SVC(kernel='poly', probability=True),
            XGBClassifier()
        ]

        for model in models:
            model.fit(X_train, Y_train)

            print(f'{model}: ')
            print('Training AUC:', metrics.roc_auc_score(
                Y_train, model.predict_proba(X_train)[:, 1]
            ))
            print('Validation AUC:', metrics.roc_auc_score(
                Y_valid, model.predict_proba(X_valid)[:, 1]
            ))
            print()

    def run_all(self):
        #self.show_graph()
        #self.plot_close_high()
        self.train_model()
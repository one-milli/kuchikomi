import pandas as pd

# CSVファイルの読み込み（エンコーディングは必要に応じて指定）
df = pd.read_csv('ozmall_reviews.csv', encoding='utf-8')

# データ件数、カラムの確認
print("データ件数:", len(df))
print("カラム一覧:", df.columns.tolist())

# 各評価項目の基本統計量
score_columns = ['overall_score', 'plan_score', 'atmosphere_score', 'food_score',
                 'cost_performance_score', 'service_score']
print(df[score_columns].describe())

# 総合評価が4.5以上のデータにフィルタリング
df_high = df[df['overall_score'] >= 4.5].copy()
print("高評価データ件数:", len(df_high))

import re
from janome.tokenizer import Tokenizer

# Janomeのトークナイザーの初期化
tokenizer = Tokenizer()

def preprocess_text(text):
    # Noneチェック、文字列変換
    if pd.isna(text):
        return ""
    # 改行や余分なスペース、特殊文字の除去（必要に応じて調整）
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\sぁ-んァ-ン一-龥]', '', text)
    return text

def tokenize_text(text):
    # 生成されるgeneratorをリストに変換する
    tokens = list(tokenizer.tokenize(text, wakati=True))
    return tokens


# 例として「comment_food_drink」の前処理と分かち書き
df_high['clean_comment_food_drink'] = df_high['comment_food_drink'].apply(preprocess_text)
df_high['tokens_food_drink'] = df_high['clean_comment_food_drink'].apply(tokenize_text)

# 同様に、他のコメント列も処理可能

# 利用目的の頻度
print(df_high['purpose'].value_counts())

# 日付形式の変換と時系列解析（必要に応じて）
df_high['date'] = pd.to_datetime(df_high['date'], format='%Y/%m/%d')
print(df_high['date'].dt.month.value_counts().sort_index())

from collections import Counter

# 全ての料理コメントの分かち書きリストを結合
all_tokens_food = sum(df_high['tokens_food_drink'].tolist(), [])
counter_food = Counter(all_tokens_food)

# 出現頻度が高い上位20語を表示
print(counter_food.most_common(20))

from sklearn.feature_extraction.text import TfidfVectorizer

# 料理関連のテキストデータの結合（各レビューを1文書として扱う）
food_texts = df_high['clean_comment_food_drink'].tolist()

# TF-IDFベクトライザーの設定（日本語の場合、事前に分かち書きしたものを結合して文字列にする）
food_texts_joined = [" ".join(tokens) for tokens in df_high['tokens_food_drink']]

vectorizer = TfidfVectorizer(max_features=100)
tfidf_matrix = vectorizer.fit_transform(food_texts_joined)
feature_names = vectorizer.get_feature_names_out()

# 各文書における上位キーワードの確認（例として、最初の5件）
import numpy as np

for idx in range(5):
    tfidf_scores = tfidf_matrix[idx].toarray().flatten()
    top_indices = np.argsort(tfidf_scores)[-5:]
    top_keywords = [feature_names[i] for i in top_indices]
    print(f"文書 {idx+1} の上位キーワード:", top_keywords)

import pandas as pd
import MeCab
from collections import Counter
import re
import os

# 1. MeCabの初期化
mecab = MeCab.Tagger(
    '-d "C:/Program Files (x86)/MeCab/dic/ipadic" '
    '-u "C:/Program Files (x86)/MeCab/dic/NEologd/NEologd.20200910-u.dic"'
)
mecab.parse("")  # バッファオーバーフロー防止のためのダミー解析

# 2. CSVファイルの読み込み
csv_file = "ozmall_reviews.csv"
try:
    df = pd.read_csv(csv_file, encoding="utf-8")  # 文字コードが異なる場合は適宜変更
except UnicodeDecodeError:
    df = pd.read_csv(csv_file, encoding="cp932")  # 日本語Windows環境の場合

# 3. 口コミコメントの取得
comments = df["comment_atmosphere_service"].dropna().astype(str).tolist()

# 4. ストップワードの定義
stopwords = {"こと", "さん", "の", "よう", "くだ"}


# 5. 名詞を抽出する関数の定義
def extract_nouns(text):
    nouns = []
    node = mecab.parseToNode(text)
    while node:
        # 形態素の品詞情報を取得
        features = node.feature.split(",")
        # 名詞（一般、固有名詞など）を抽出
        if features[0] == "名詞" and features[1] not in ["代名詞", "接続詞的"]:
            noun = node.surface
            # 不要な記号や数字を除外
            if re.match(r"^[\w一-龥ぁ-んァ-ン]+$", noun):
                # ストップワードに含まれていない場合のみ追加
                if noun not in stopwords:
                    nouns.append(noun)
        node = node.next
    return nouns


# 6. すべての名詞を収集
all_nouns = []
for comment in comments:
    all_nouns.extend(extract_nouns(comment))

# 7. 名詞の頻度をカウント
noun_counts = Counter(all_nouns)

# 8. 頻出名詞の上位N件を取得（例: 上位20件）
top_n = 50
top_nouns = [noun for noun, count in noun_counts.most_common(top_n)]

print(f"上位{top_n}の頻出名詞:")
for noun, count in noun_counts.most_common(top_n):
    print(f"{noun}: {count}回")

# 9. 保存するCSVファイルに含めるカラムの定義
columns_to_save = [
    "restaurant_name",
    "user_name",
    "age_gender",
    "usage_count",
    "date",
    "purpose",
    "overall_score",
    "plan_score",
    "atmosphere_score",
    "food_score",
    "cost_performance_score",
    "service_score",
    "plan_menu",
    "comment_atmosphere_service",
]

# 10. 出力ディレクトリの作成
output_dir = "noun_reviews_csv"
os.makedirs(output_dir, exist_ok=True)

# 11. 口コミコメントを辞書形式に追加（後で形態素解析結果を保存）
# パフォーマンス向上のため、コメントごとに一度だけ形態素解析を行う
df["extracted_nouns"] = df["comment_atmosphere_service"].apply(extract_nouns)

# 12. 名詞ごとに該当する口コミを抽出し、CSVに保存
for noun in top_nouns:
    # 名詞が含まれる口コミをフィルタリング
    filtered_df = df[df["extracted_nouns"].apply(lambda nouns: noun in nouns)]

    # フィルタリングされたデータフレームが空でない場合に保存
    if not filtered_df.empty:
        # 必要なカラムのみを抽出
        filtered_df_to_save = filtered_df[columns_to_save]

        # ファイル名の作成（例: noun_寿司_reviews.csv）
        # ファイル名に使用できない文字を置換
        safe_noun = re.sub(r'[\\/*?:"<>|]', "_", noun)
        output_file = os.path.join(output_dir, f"noun_{safe_noun}_reviews.csv")

        # CSVに保存
        try:
            filtered_df_to_save.to_csv(output_file, index=False, encoding="utf-8-sig")
            print(f"名詞「{noun}」に該当する口コミを '{output_file}' に保存しました。")
        except Exception as e:
            print(f"名詞「{noun}」のCSV保存中にエラーが発生しました: {e}")
    else:
        print(f"名詞「{noun}」に該当する口コミはありませんでした。")

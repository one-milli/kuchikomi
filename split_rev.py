import pandas as pd
import MeCab
import os
import re

# MeCabの初期化
mecab = MeCab.Tagger(
    '-d "C:/Program Files (x86)/MeCab/dic/ipadic" -u "C:/Program Files (x86)/MeCab/dic/NEologd/NEologd.20200910-u.dic"'
)

# CSVファイルの読み込み
# エンコーディングが異なる場合は適宜変更してください（例： 'utf-8-sig', 'shift_jis' など）
df = pd.read_csv("ozmall_reviews.csv", encoding="utf-8")

# age_genderカラムの存在を確認
if "age_gender" not in df.columns:
    raise ValueError("CSVファイルに 'age_gender' カラムが存在しません。")


# 年齢情報を抽出する関数
def extract_age_group(age_gender_str):
    """
    'age_gender' カラムから年齢情報を抽出します。
    例:
        "20代前半（女）" -> "20代前半"
        "10代（女）" -> "10代"
        "70代以上（女）" -> "70代以上"
    """
    match = re.match(r"(\d+代(?:前半|後半)?|70代以上)", age_gender_str)
    if match:
        return match.group(1)
    else:
        return "不明"


# 新しいカラム 'age_group' を作成
df["age_group"] = df["age_gender"].apply(extract_age_group)

# 出力先ディレクトリの作成
output_dir = "split_reviews_by_age"
os.makedirs(output_dir, exist_ok=True)

# 年代ごとにデータを分割して保存
unique_age_groups = df["age_group"].unique()

for age_group in unique_age_groups:
    # フィルタリング
    subset = df[df["age_group"] == age_group]

    # ファイル名に使用できない文字を置換
    # ここでは日本語の特殊文字をアンダースコアに置換
    safe_age_group = re.sub(r'[\/:*?"<>|（）\s]', "_", age_group)

    # ファイルパスの作成
    filename = f"reviews_{safe_age_group}.csv"
    file_path = os.path.join(output_dir, filename)

    # CSVとして保存
    subset.to_csv(file_path, index=False, encoding="cp932")

    print(f"Saved {len(subset)} records to {file_path}")

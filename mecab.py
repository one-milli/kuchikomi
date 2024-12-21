import re
import pandas as pd
import MeCab
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


try:
    df = pd.read_csv("worse_ozmall_reviews.csv")
    print("CSVファイルの読み込みに成功しました。")
except Exception as e:
    print("CSVファイルの読み込み中にエラーが発生しました:", e)
    exit()

col_name = "comment_food_drink"
# col_name = "comment_atmosphere_service"

if col_name in df.columns:
    print(f"'{col_name}'カラムが見つかりました。")
    print("最初の5件のコメントを表示します:")
    print(df[col_name].head())
else:
    print(f"エラー: '{col_name}'カラムが見つかりません。CSVファイルのカラム名を確認してください。")
    exit()

try:
    mecab = MeCab.Tagger(
        '-d "C:/Program Files (x86)/MeCab/dic/ipadic" -u "C:/Program Files (x86)/MeCab/dic/NEologd/NEologd.20200910-u.dic"'
    )
    print("MeCabの初期化に成功しました。")
except Exception as e:
    print("MeCabの初期化中にエラーが発生しました:", e)
    exit()

# 3. トークナイズ関数の定義とテスト
stop_words = [
    "の",
    "に",
    "は",
    "を",
    "た",
    "が",
    "で",
    "て",
    "と",
]

# 形態素解析結果を保存するリストを初期化
all_morphs = []


# 前処理関数の定義
def preprocess(text):
    # 半角スペース、全角スペース、数字、記号を除去
    # text = re.sub(r"[0-9０-９]", "", text)
    text = re.sub(r"[!-/:-@[-`{-~]", "", text)  # 半角記号
    text = re.sub(r"\s+", "", text)  # 空白の除去
    return text


def tokenize(text):
    tokens = []
    text = preprocess(text)
    parsed = mecab.parse(text)

    if parsed is None:
        print("MeCabの解析結果がNoneです。")
        return tokens

    for line in parsed.splitlines():
        if line == "EOS" or line == "":
            break
        try:
            surface, feature = line.split("\t")[:2]
            features = feature.split(",")
            pos = features[0]  # 品詞
            pos_sub1 = features[1]  # 品詞細分類1
            if pos_sub1 == "固有名詞":
                base_form = surface
            else:
                base_form = (
                    features[6] if (len(features) > 6) else surface
                )  # 基本形が存在する場合は取得、なければ表層形を使用
            if base_form == "Afternoon tea":
                base_form = "アフタヌーンティー"

            # if pos in ["名詞", "形容詞", "副詞"]:
            # if base_form not in stop_words:
            tokens.append(base_form)

            # 形態素解析結果をリストに追加
            all_morphs.append({"surface": surface, "feature": feature})

        except ValueError as ve:
            print(f"解析エラー行: {line} - {ve}")

    return tokens


# 年代を抽出する関数
def extract_age_group(age_gender_str):
    """
    age_gender_str: 例 "20代前半（女）"
    戻り値: "20代前半"
    """
    match = re.match(r"(\d+代[^\（]+)", age_gender_str)
    if match:
        return match.group(1)
    else:
        return "10代"  # パターンに合わない場合


def sort_key(age_group):
    """
    年代グループをソートするためのキーを生成します。

    Args:
        age_group (str): 例 "20代前半"

    Returns:
        tuple: (年代の数値, 半期の順序)
    """
    match = re.match(r"(\d+)代(前半|後半)", age_group)
    if match:
        decade = int(match.group(1))
        half = 0 if match.group(2) == "前半" else 1
        return (decade, half)
    else:
        return (999, 0)  # パターンに合わない場合は最後に配置


# 全コメントから単語を抽出
MAX_NUM = 50
all_tokens = []
for idx, comment in enumerate(df[col_name]):
    if isinstance(comment, str):
        tokens = tokenize(comment)
        all_tokens.extend(tokens)
    else:
        print(f"コメントが文字列ではありません: インデックス {idx}, 内容: {comment}")

print(f"\n全コメントから抽出された総単語数: {len(all_tokens)}")

# 形態素解析結果をDataFrameに変換
morph_df = pd.DataFrame(all_morphs)

# CSVに保存
morph_csv_filename = "morphological_analysis.csv"
try:
    morph_df.to_csv(morph_csv_filename, index=False, encoding="utf-8-sig")
    print(f"形態素解析結果を '{morph_csv_filename}' に保存しました。")
except Exception as e:
    print(f"形態素解析結果の保存中にエラーが発生しました: {e}")

exit()

# 単語の頻度をカウント
word_counts = Counter(all_tokens)
print(f"ユニークな単語数: {len(word_counts)}")

# 頻出単語が存在しない場合の対処
if not word_counts:
    print("エラー: 単語のカウントが空です。前処理やトークナイズのステップを再確認してください。")
    exit()

# 結果の可視化（棒グラフとワードクラウド）
top = word_counts.most_common(MAX_NUM)
top_words = [word for word, count in top]

# 共起関係を保存する辞書
co_occurrence = defaultdict(Counter)

for comment in df[col_name]:
    if isinstance(comment, str):
        tokens = tokenize(comment)
        tokens_set = set(tokens)  # 重複を避けるためにセット化
        for word in top_words:
            if word in tokens_set:
                for co_word in tokens_set:
                    if co_word != word:
                        co_occurrence[word][co_word] += 1

# 共起結果の表示
for word, counter in co_occurrence.items():
    print(f"'{word}' に関連する頻出単語:")
    for co_word, count in counter.most_common(10):
        print(f"  {co_word}: {count}")
    print()

font_path = "ipaexg.ttf"
font_prop = fm.FontProperties(fname=font_path)

# 棒グラフの作成
words, counts = zip(*top)
plt.figure(figsize=(10, 8))
plt.barh(words, counts, color="skyblue")
plt.xlabel("出現回数", fontproperties=font_prop)
plt.title(f"上位{MAX_NUM}頻出単語", fontproperties=font_prop)
plt.gca().invert_yaxis()  # 上位が上に来るように
plt.yticks(fontproperties=font_prop)
plt.show()

# 年代別に頻出単語を集計
# "age_gender"カラムには年代と性別が含まれている(例: "20代前半（女）")
if "age_gender" in df.columns:
    # 新しいカラム 'age_group' を作成
    df["age_group"] = df["age_gender"].apply(extract_age_group)
    print("\n'age_group' カラムを作成しました。")
    print("年代ごとのコメント数:")
    print(df["age_group"].value_counts())
else:
    print("エラー: 'age_gender' カラムが見つかりません。")
    exit()

# 年代別に頻出単語を集計
age_groups = df["age_group"].unique()
age_groups = sorted(age_groups, key=sort_key)
age_word_counts = defaultdict(Counter)

for age in age_groups:
    # 年代グループごとにデータをフィルタリング
    subset = df[df["age_group"] == age]
    print(f"\n年代: {age} のコメント数: {len(subset)}")

    # 各コメントから単語を抽出し、カウント
    tokens = []
    for comment in subset[col_name]:
        if isinstance(comment, str):
            tokens.extend(tokenize(comment))

    # 単語の頻度をカウント
    word_counts_age = Counter(tokens)
    age_word_counts[age] = word_counts_age
    print(f"'{age}' の上位10頻出単語: {word_counts_age.most_common(20)}")

# 結果の可視化（年代別の棒グラフ）
for age, counter in age_word_counts.items():
    top_n = 20  # 上位10単語を表示
    top_words = counter.most_common(top_n)
    words, counts = zip(*top_words) if top_words else ([], [])

    plt.figure(figsize=(10, 8))
    plt.barh(words, counts, color="skyblue")
    plt.xlabel("出現回数", fontproperties=fm.FontProperties(fname=font_path))
    plt.title(f"{age} の上位{top_n}頻出単語", fontproperties=fm.FontProperties(fname=font_path))
    plt.gca().invert_yaxis()  # 上位が上に来るように
    plt.yticks(fontproperties=fm.FontProperties(fname=font_path))
    plt.show()

print("")
print("すべての単語の出現頻度を 'word_frequencies.csv' に保存します。")
# すべての単語を頻度順にソート
sorted_word_freq = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

# データフレームを作成
df_word_freq = pd.DataFrame(sorted_word_freq, columns=["word", "frequency"])

# CSVに保存
df_word_freq.to_csv("word_frequencies.csv", index=False, encoding="utf-8-sig")
print("保存が完了しました。")

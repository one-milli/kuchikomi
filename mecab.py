import re
import pandas as pd
import MeCab
import ipadic
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from wordcloud import WordCloud


try:
    df = pd.read_csv("ozmall_reviews.csv")
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
    mecab = MeCab.Tagger(ipadic.MECAB_ARGS)
    print("MeCabの初期化に成功しました。")
except Exception as e:
    print("MeCabの初期化中にエラーが発生しました:", e)
    exit()

# 3. トークナイズ関数の定義とテスト
stop_words = [
    "*",
    "の",
    "に",
    "は",
    "を",
    "た",
    "が",
    "で",
    "て",
    "と",
    "する",
    "ます",
    "し",
    "こと",
    "も",
    "さ",
    "ん",
    "ない",
    "いる",
    "れ",
    "られ",
    "もの",
    "なる",
    "ある",
]


# 3. 前処理関数の定義
def preprocess(text):
    # 半角スペース、全角スペース、数字、記号を除去
    text = re.sub(r"[0-9０-９]", "", text)
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
            base_form = (
                features[6] if len(features) > 6 else surface
            )  # 基本形が存在する場合は取得、なければ表層形を使用

            if pos in ["名詞", "形容詞", "副詞"]:
                if base_form not in stop_words:
                    tokens.append(base_form)
        except ValueError as ve:
            print(f"解析エラー行: {line} - {ve}")

    return tokens


# 4. 全コメントから単語を抽出
MAX_NUM = 50
all_tokens = []
for idx, comment in enumerate(df[col_name]):
    if isinstance(comment, str):
        tokens = tokenize(comment)
        all_tokens.extend(tokens)
    else:
        print(f"コメントが文字列ではありません: インデックス {idx}, 内容: {comment}")

print(f"\n全コメントから抽出された総単語数: {len(all_tokens)}")
print(f"最初の{MAX_NUM}単語を表示:", all_tokens[:MAX_NUM])

# 5. 単語の頻度をカウント
word_counts = Counter(all_tokens)
print(f"ユニークな単語数: {len(word_counts)}")
print(f"上位{MAX_NUM}頻出単語:", word_counts.most_common(MAX_NUM))

# 6. 頻出単語が存在しない場合の対処
if not word_counts:
    print("エラー: 単語のカウントが空です。前処理やトークナイズのステップを再確認してください。")
    exit()

# 7. 結果の可視化（棒グラフとワードクラウド）
top_20 = word_counts.most_common(MAX_NUM)

font_path = "ipaexg.ttf"
font_prop = fm.FontProperties(fname=font_path)

# 棒グラフの作成
words, counts = zip(*top_20)
plt.figure(figsize=(10, 8))
plt.barh(words, counts, color="skyblue")
plt.xlabel("出現回数", fontproperties=font_prop)
plt.title(f"上位{MAX_NUM}頻出単語", fontproperties=font_prop)
plt.gca().invert_yaxis()  # 上位が上に来るように
plt.yticks(fontproperties=font_prop)
plt.show()

# ワードクラウドの作成
word_freq = dict(word_counts.most_common(100))
wordcloud = WordCloud(font_path=font_path, background_color="white", width=800, height=600).generate_from_frequencies(
    word_freq
)

plt.figure(figsize=(10, 8))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.show()

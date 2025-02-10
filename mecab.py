import os
import re
import pandas as pd
import MeCab
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


# シズルワードリストの読み込み関数
def load_sizzle_words(file_path, mecab):
    sizzle_words = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word:
                    tokens = tokenize(word, mecab)
                    if tokens:
                        sizzle_words.append({"word": word, "tokens": tokens})
        print(f"シズルワードリストを '{file_path}' から読み込みました。総シズルワード数: {len(sizzle_words)}")
        # デバッグ用に最初の3つを表示
        if len(sizzle_words) > 0:
            print("サンプルシズルワード:", sizzle_words[:3])
    except Exception as e:
        print(f"シズルワードリストの読み込み中にエラーが発生しました: {e}")
        exit()
    return sizzle_words


# 前処理関数の定義
def preprocess(text):
    # 半角記号を除去（ただし '%' は除外）
    text = re.sub(r'[!"#$&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]', "", text)
    # 空白の除去
    text = re.sub(r"\s+", "", text)
    return text


# トークナイズ関数の定義
def tokenize(text, mecab):
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

            tokens.append(base_form)

        except ValueError as ve:
            print(f"解析エラー行: {line} - {ve}")

    return tokens


# CSVファイルの読み込み
def load_reviews(csv_path, required_columns):
    try:
        df = pd.read_csv(csv_path)
        print("CSVファイルの読み込みに成功しました。")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp932")  # 日本語Windows環境の場合
    except Exception as e:
        print("CSVファイルの読み込み中にエラーが発生しました:", e)
        exit()

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"エラー: 以下の必要なカラムがCSVファイルに見つかりません: {missing_columns}")
        exit()
    else:
        print("全ての必要なカラムが見つかりました。")

    print("最初の5件のコメントを表示します:")
    print(df[required_columns].head())
    return df


# 設定
suffix = "70代"
# csv_file = f"split_reviews_by_age/reviews_{suffix}.csv"
csv_file = f"ozmall_reviews_10.csv"
required_columns = [
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
    "comment_food_drink",  # 口コミのカラム名
]
col_name = "comment_food_drink"  # 口コミのカラム名
sizzle_word_file = "sizzle_1.txt"  # シズルワードリストのファイル名
# output_dir = f"split_reviews_by_age/matched_reviews_by_sizzle_{suffix}"  # 出力ディレクトリ名
output_dir = f"out"  # 出力ディレクトリ名

# CSVからコメントを読み込む
df = load_reviews(csv_file, required_columns)

# MeCabの初期化
try:
    mecab = MeCab.Tagger(
        '-d "C:/Program Files (x86)/MeCab/dic/ipadic" -u "C:/Program Files (x86)/MeCab/dic/NEologd/NEologd.20200910-u.dic"'
    )
except Exception as e:
    print("MeCabの初期化中にエラーが発生しました:", e)
    exit()

# シズルワードリストの読み込み
sizzle_words = load_sizzle_words(sizzle_word_file, mecab)

# シズルワードごとのマッチした口コミを保存する辞書を初期化
matched_comments_dict = defaultdict(list)
for sizzle in sizzle_words:
    matched_comments_dict[sizzle["word"]] = []

# 全コメントからマッチする口コミを抽出
for idx, row in df.iterrows():
    comment = row[col_name]
    if isinstance(comment, str):
        tokens = tokenize(comment, mecab)

        for sizzle in sizzle_words:
            sizzle_word = sizzle["word"]
            sizzle_tokens = sizzle["tokens"]
            sizzle_len = len(sizzle_tokens)
            if sizzle_len == 0:
                continue
            # スライディングウィンドウでマッチング
            for i in range(len(tokens) - sizzle_len + 1):
                if tokens[i : i + sizzle_len] == sizzle_tokens:
                    print(comment)
                    print(tokens)
                    print(sizzle_tokens)
                    # 必要なカラムを抽出
                    matched_row = row[required_columns].to_dict()
                    matched_comments_dict[sizzle_word].append(matched_row)
                    break  # このシズルワードでマッチしたら次のシズルワードへ
    else:
        print(f"コメントが文字列ではありません: インデックス {idx}, 内容: {comment}")

# マッチした口コミの総数を表示
total_matched = sum(len(comments) for comments in matched_comments_dict.values())
print(f"\nシズルワードを含む口コミの総数: {total_matched}")

exit()

# 出力ディレクトリを作成
os.makedirs(output_dir, exist_ok=True)

# シズルワードごとの口コミを個別のCSVファイルに保存
for sizzle_word, comments in matched_comments_dict.items():
    if comments:
        # ファイル名にシズルワードを使用する場合、ファイル名に使えない文字を置換
        safe_sizzle_word = re.sub(r'[\\/*?:"<>|]', "_", sizzle_word)
        filename = os.path.join(output_dir, f"matched_reviews_{safe_sizzle_word}.csv")
        matched_df = pd.DataFrame(comments)
        try:
            matched_df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"シズルワード '{sizzle_word}' を含む口コミを '{filename}' に保存しました。")
        except Exception as e:
            print(f"シズルワード '{sizzle_word}' の口コミ保存中にエラーが発生しました: {e}")
    else:
        print(f"シズルワード '{sizzle_word}' を含む口コミはありませんでした。")

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

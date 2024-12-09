import ast


def extract_matching_entries(input_file, keywords_file):
    """
    input_file: str - パス to input.txt ファイル
    keywords_file: str - パス to keywords.txt ファイル
    Returns: list of tuples - 抜き出されたタプルのリスト
    """
    # キーワードをセットとして読み込む（高速な検索のため）
    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = set(line.strip() for line in f if line.strip())

    # 入力ファイルの内容を読み込む
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # 入力がリスト形式でない場合、リストに括る
    if not content.startswith("["):
        content = "[" + content + "]"

    try:
        # タプルのリストとして解析
        entries = ast.literal_eval(content)
    except Exception as e:
        print("入力ファイルの解析中にエラーが発生しました:", e)
        return []

    # キーワードと一致するエントリを抽出
    matches = [entry for entry in entries if entry[0] in keywords]

    return matches


def main():
    # ファイル名を指定
    input_file = "all_words.txt"
    keywords_file = "sizzle_words.txt"

    # 一致するエントリを抽出
    matches = extract_matching_entries(input_file, keywords_file)

    # 結果を出力
    for match in matches:
        print(match)


if __name__ == "__main__":
    main()

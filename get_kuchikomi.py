import csv
import time
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# レビューを取得したいレストランのURLリスト
# restaurant_urls = [
#     "https://www.ozmall.co.jp/restaurant/3288/review/",
#     "https://www.ozmall.co.jp/restaurant/3289/review/",
#     # ... 100店舗分のURLを追加
# ]

UNKNOWN = "Unknown"
MAX_REVIEWS = 20

# CSVファイルに保存するための準備
with open("ozmall_reviews.csv", "w", newline="", encoding="utf-8-sig") as csvfile:
    fieldnames = [
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
        "comment_food_drink",
        "comment_atmosphere_service",
        "comment_reactions",
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # セッションの設定（リトライやヘッダーの統一に役立ちます）
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    # for url in restaurant_urls:
    url = "https://www.ozmall.co.jp/restaurant/3288/review/"
    try:
        print(f"Processing restaurant URL: {url}")
        # ページ番号の初期化
        PAGE_NO = 1
        REVIEW_COUNT = 0
        while True:
            # ページURLの構築
            if PAGE_NO == 1:
                PAGE_URL = url  # 最初のページは基本URL
            else:
                # ページURLに?pageNo=2#resultのように追加
                PAGE_URL = urljoin(url, f"?pageNo={PAGE_NO}#result")

            print(f"  Processing page {PAGE_NO}: {PAGE_URL}")

            # HTTPリクエストを送信
            response = session.get(PAGE_URL)
            if response.status_code != 200:
                print(f"    Failed to retrieve {PAGE_URL}: Status code {response.status_code}")
                break  # 次のレストランへ移行

            # HTMLを解析
            soup = BeautifulSoup(response.text, "html.parser")

            # レストラン名の取得（最初のページのみ）
            if PAGE_NO == 1:
                restaurant_name_tag = soup.find("div", class_="shop-name")
                if restaurant_name_tag:
                    h1_tag = restaurant_name_tag.find("h1")
                    if h1_tag:
                        a_tag = h1_tag.find("a")
                        if a_tag:
                            # レストラン名の抽出（スパン以降を除去）
                            restaurant_name = a_tag.get_text(strip=True).split("[")[0]
                        else:
                            restaurant_name = UNKNOWN
                    else:
                        restaurant_name = UNKNOWN
                else:
                    restaurant_name = UNKNOWN

            # 口コミ一覧の取得
            review_lists = soup.find_all("div", class_="review__list")
            if not review_lists:
                print(f"    No reviews found on {PAGE_URL}")
                break  # レビューがない場合、次のレストランへ

            # `review__list` の中から `common-frame` を含まないものを選択
            for review_list in review_lists:
                classes = review_list.get("class", [])
                if "common-frame" in classes:
                    # この `review__list` は無視
                    continue
                # ここからが対象の `review__list`
                # 口コミボックスの取得（10件）
                review_boxes = review_list.find_all("div", class_="review__list--box", limit=10)
                if not review_boxes:
                    print(f"    No review boxes found on {PAGE_URL}")
                    continue  # 次の `review__list` へ

                for review_box in review_boxes:
                    # ユーザー情報の取得
                    user_info = review_box.find("div", class_="review__list--box__cell")
                    if user_info:
                        user_name_tag = user_info.find("div", class_="review__list--box__user")
                        if user_name_tag:
                            p_tags = user_name_tag.find_all("p")
                            USER_NAME = p_tags[0].get_text(strip=True) if len(p_tags) > 0 else UNKNOWN
                            AGE_GENDER = p_tags[1].get_text(strip=True) if len(p_tags) > 1 else UNKNOWN
                        else:
                            USER_NAME = UNKNOWN
                            AGE_GENDER = UNKNOWN

                        # ユーザー詳細データの取得
                        user_data = user_info.find("dl", class_="review__list--box__user-data")
                        if user_data:
                            dt_tags = user_data.find_all("dt")
                            dd_tags = user_data.find_all("dd")
                            user_data_dict = {}
                            for dt, dd in zip(dt_tags, dd_tags):
                                key = dt.get_text(strip=True)
                                value = dd.get_text(strip=True)
                                user_data_dict[key] = value
                            USAGE_COUNT = user_data_dict.get("利用人数", UNKNOWN)
                            DATE = user_data_dict.get("投稿日", UNKNOWN)
                            PURPOSE = user_data_dict.get("利用目的", UNKNOWN)
                        else:
                            USAGE_COUNT = UNKNOWN
                            DATE = UNKNOWN
                            PURPOSE = UNKNOWN
                    else:
                        USER_NAME = UNKNOWN
                        AGE_GENDER = UNKNOWN
                        USAGE_COUNT = UNKNOWN
                        DATE = UNKNOWN
                        PURPOSE = UNKNOWN

                    # 口コミ詳細の取得
                    review_detail = review_box.find_all("div", class_="review__list--box__cell")
                    if len(review_detail) < 2:
                        # 期待されるセル数が不足している場合
                        continue

                    # 口コミのスコア部分
                    score_section = review_detail[1].find("div", class_="review__list--box__score")
                    if score_section:
                        # 総合スコアの取得
                        total_score_section = score_section.find("dl", class_="review__list--box__score--total")
                        if total_score_section:
                            overall_score = total_score_section.find("span", class_="review-totalscore").get_text(
                                strip=True
                            )
                        else:
                            overall_score = UNKNOWN

                        # 各カテゴリーのスコア取得
                        category_scores = score_section.find_all("dl", class_="review__list--box__score--categoryScore")
                        scores = {}
                        for category in category_scores:
                            dt = category.find("dt").get_text(strip=True)
                            dd = category.find("dd", class_="score").get_text(strip=True)
                            scores[dt] = dd
                        plan_score = scores.get("プラン", UNKNOWN)
                        atmosphere_score = scores.get("雰囲気", UNKNOWN)
                        food_score = scores.get("料理", UNKNOWN)
                        cost_performance_score = scores.get("コスパ", UNKNOWN)
                        service_score = scores.get("サービス", UNKNOWN)
                    else:
                        overall_score = UNKNOWN
                        plan_score = UNKNOWN
                        atmosphere_score = UNKNOWN
                        food_score = UNKNOWN
                        cost_performance_score = UNKNOWN
                        service_score = UNKNOWN

                    # 利用プラン情報の取得
                    plan_section = review_detail[1].find("div", class_="review__list--box__plan--text")
                    if plan_section:
                        plan_title_tag = plan_section.find("p", class_="review__list--box__plan--title")
                        plan_menu_tag = plan_section.find("p", class_="review__list--box__plan--menu")
                        plan_menu = plan_menu_tag.get_text(strip=True) if plan_menu_tag else UNKNOWN
                    else:
                        plan_menu = UNKNOWN

                    # コメントの取得
                    comments = review_detail[1].find_all("dl", class_="review__list--box__comment")
                    comment_food_drink = UNKNOWN
                    comment_atmosphere_service = UNKNOWN
                    comment_reactions = UNKNOWN
                    for comment in comments:
                        heading = comment.find("dt", class_="review__list--box__comment--heading").get_text(strip=True)
                        content = comment.find("dd").get_text(strip=True)
                        if heading == "食事やドリンクについて":
                            comment_food_drink = content
                        elif heading == "店の雰囲気やサービスについて":
                            comment_atmosphere_service = content
                        elif heading == "一緒に行った相手の反応について":
                            comment_reactions = content

                    # データの書き込み
                    writer.writerow(
                        {
                            "restaurant_name": restaurant_name,
                            "user_name": USER_NAME,
                            "age_gender": AGE_GENDER,
                            "usage_count": USAGE_COUNT,
                            "date": DATE,
                            "purpose": PURPOSE,
                            "overall_score": overall_score,
                            "plan_score": plan_score,
                            "atmosphere_score": atmosphere_score,
                            "food_score": food_score,
                            "cost_performance_score": cost_performance_score,
                            "service_score": service_score,
                            "plan_menu": plan_menu,
                            "comment_food_drink": comment_food_drink,
                            "comment_atmosphere_service": comment_atmosphere_service,
                            "comment_reactions": comment_reactions,
                        }
                    )
                    REVIEW_COUNT += 1
                    if REVIEW_COUNT >= MAX_REVIEWS:
                        break

                if REVIEW_COUNT >= MAX_REVIEWS:
                    break

            if REVIEW_COUNT >= MAX_REVIEWS:
                break  # 10件以上のレビューがある場合、次のレストランへ

            # ページネーションの確認
            pager = soup.find("div", class_="pager")
            if pager:
                pager_count = pager.find("ul", class_="pager__count")
                if pager_count:
                    # 全てのページリンクを取得
                    page_links = pager_count.find_all("a")
                    page_numbers = []
                    for link in page_links:
                        href = link.get("href", "")
                        # 正規表現でpageNoの値を抽出
                        match = re.search(r"pageNo=(\d+)", href)
                        if match:
                            page_num = int(match.group(1))
                            page_numbers.append(page_num)
                    if page_numbers:
                        max_page = max(page_numbers)
                        if PAGE_NO < max_page:
                            PAGE_NO += 1
                        else:
                            break  # 最後のページに到達
                    else:
                        break  # ページリンクがない場合
                else:
                    break  # pager__countがない場合
            else:
                break  # pagerがない場合

            # サーバーへの負荷を避けるために待機
            time.sleep(1)

    except Exception as e:
        print(f"Error processing {url}: {e}")
        exit()

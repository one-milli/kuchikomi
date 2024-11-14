import csv
import time
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

UNKNOWN = "Unknown"
MAX_REVIEWS = 15

# 口コミを取得したいレストランのURLリストをファイルから読み込む
with open("restaurant_urls_partial.csv", "r", encoding="utf-8-sig") as url_file:
    restaurant_urls = [line.strip().replace("/afternoontea/", "/review/") for line in url_file if line.strip()]

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

    for URL in restaurant_urls:
        try:
            print(f"Processing restaurant URL: {URL}")
            # ページ番号の初期化
            PAGE_NO = 1
            REVIEW_COUNT = 0
            while True:
                # ページURLの構築
                if PAGE_NO == 1:
                    PAGE_URL = URL  # 最初のページは基本URL
                else:
                    # ページURLに?pageNo=2#resultのように追加
                    PAGE_URL = urljoin(URL, f"?pageNo={PAGE_NO}#result")

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
                                RESTAURANT_NAME = a_tag.get_text(strip=True).split("[")[0]
                            else:
                                RESTAURANT_NAME = UNKNOWN
                        else:
                            RESTAURANT_NAME = UNKNOWN
                    else:
                        RESTAURANT_NAME = UNKNOWN

                # 口コミ一覧の取得
                review_lists = soup.find_all("div", class_="review__list")
                if not review_lists:
                    print(f"    No reviews found on {PAGE_URL}")
                    break  # レビューがない場合、次のレストランへ

                # `review__list` の中から `common-frame` を含まないものを選択
                for review_list in review_lists:
                    classes = review_list.get("class", [])
                    if "common-frame" in classes:
                        continue

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
                                user_data_dict = {
                                    dt.get_text(strip=True): dd.get_text(strip=True) for dt, dd in zip(dt_tags, dd_tags)
                                }
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
                            continue

                        # 口コミのスコア部分
                        score_section = review_detail[1].find("div", class_="review__list--box__score")
                        if score_section:
                            total_score_section = score_section.find("dl", class_="review__list--box__score--total")
                            OVERALL_SCORE = (
                                total_score_section.find("span", class_="review-totalscore").get_text(strip=True)
                                if total_score_section
                                else UNKNOWN
                            )

                            category_scores = score_section.find_all(
                                "dl", class_="review__list--box__score--categoryScore"
                            )
                            scores = {
                                category.find("dt")
                                .get_text(strip=True): category.find("dd", class_="score")
                                .get_text(strip=True)
                                for category in category_scores
                            }
                            PLAN_SCORE = scores.get("プラン", UNKNOWN)
                            ATMOSPHERE_SCORE = scores.get("雰囲気", UNKNOWN)
                            FOOD_SCORE = scores.get("料理", UNKNOWN)
                            COST_PERFORMANCE_SCORE = scores.get("コスパ", UNKNOWN)
                            SERVICE_SCORE = scores.get("サービス", UNKNOWN)
                        else:
                            OVERALL_SCORE = UNKNOWN
                            PLAN_SCORE = UNKNOWN
                            ATMOSPHERE_SCORE = UNKNOWN
                            FOOD_SCORE = UNKNOWN
                            COST_PERFORMANCE_SCORE = UNKNOWN
                            SERVICE_SCORE = UNKNOWN

                        # 利用プラン情報の取得
                        plan_section = review_detail[1].find("div", class_="review__list--box__plan--text")
                        PLAN_MENU = (
                            plan_section.find("p", class_="review__list--box__plan--menu").get_text(strip=True)
                            if plan_section and plan_section.find("p", class_="review__list--box__plan--menu")
                            else UNKNOWN
                        )

                        # コメントの取得
                        comments = review_detail[1].find_all("dl", class_="review__list--box__comment")
                        COMMENT_FOOD_DRINK = COMMENT_ATMOSPHERE_SERVICE = COMMENT_REACTIONS = UNKNOWN
                        for comment in comments:
                            heading = comment.find("dt", class_="review__list--box__comment--heading").get_text(
                                strip=True
                            )
                            content = comment.find("dd").get_text(strip=True)
                            if heading == "食事やドリンクについて":
                                COMMENT_FOOD_DRINK = content
                            elif heading == "店の雰囲気やサービスについて":
                                COMMENT_ATMOSPHERE_SERVICE = content
                            elif heading == "一緒に行った相手の反応について":
                                COMMENT_REACTIONS = content

                        # データの書き込み
                        writer.writerow(
                            {
                                "restaurant_name": RESTAURANT_NAME,
                                "user_name": USER_NAME,
                                "age_gender": AGE_GENDER,
                                "usage_count": USAGE_COUNT,
                                "date": DATE,
                                "purpose": PURPOSE,
                                "overall_score": OVERALL_SCORE,
                                "plan_score": PLAN_SCORE,
                                "atmosphere_score": ATMOSPHERE_SCORE,
                                "food_score": FOOD_SCORE,
                                "cost_performance_score": COST_PERFORMANCE_SCORE,
                                "service_score": SERVICE_SCORE,
                                "plan_menu": PLAN_MENU,
                                "comment_food_drink": COMMENT_FOOD_DRINK,
                                "comment_atmosphere_service": COMMENT_ATMOSPHERE_SERVICE,
                                "comment_reactions": COMMENT_REACTIONS,
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
                        page_links = pager_count.find_all("a")
                        page_numbers = [
                            int(re.search(r"pageNo=(\d+)", link.get("href", "")).group(1))
                            for link in page_links
                            if re.search(r"pageNo=(\d+)", link.get("href", ""))
                        ]
                        if page_numbers and PAGE_NO < max(page_numbers):
                            PAGE_NO += 1
                        else:
                            break  # 最後のページに到達
                    else:
                        break  # pager__countがない場合
                else:
                    break  # pagerがない場合

                # サーバーへの負荷を避けるために待機
                time.sleep(1)

        except Exception as e:
            print(f"Error processing {URL}: {e}")
            continue

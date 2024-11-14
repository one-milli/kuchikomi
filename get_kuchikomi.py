import requests
from bs4 import BeautifulSoup
import csv
import time

# レビューを取得したいレストランのURLリスト
# restaurant_urls = [
#     "https://www.ozmall.com/restaurant1",
#     "https://www.ozmall.com/restaurant2",
#     # ... 100店舗分のURLを追加
# ]

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

    # for url in restaurant_urls:
    url = "https://www.ozmall.co.jp/restaurant/3288/review/"
    try:
        # HTTPリクエストを送信
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"Failed to retrieve {url}: Status code {response.status_code}")
            exit()

        # HTMLを解析
        soup = BeautifulSoup(response.text, "html.parser")

        # レストラン名の取得
        restaurant_name_tag = soup.find("div", class_="shop-name")
        if restaurant_name_tag:
            h1_tag = restaurant_name_tag.find("h1")
            if h1_tag:
                a_tag = h1_tag.find("a")
                if a_tag:
                    restaurant_name = a_tag.get_text(strip=True).split("[")[0]  # スパン以降を除去
                else:
                    restaurant_name = "Unknown"
            else:
                restaurant_name = "Unknown"
        else:
            restaurant_name = "Unknown"

        # 口コミ一覧の取得
        review_list = soup.find("div", class_="review__list")
        if not review_list:
            print(f"No reviews found for {url}")
            exit()

        # 口コミボックスの取得（10件）
        review_boxes = review_list.find_all("div", class_="review__list--box", limit=10)

        for review_box in review_boxes:
            # ユーザー情報の取得
            user_info = review_box.find("div", class_="review__list--box__cell")
            if user_info:
                user_name_tag = user_info.find("div", class_="review__list--box__user")
                if user_name_tag:
                    p_tags = user_name_tag.find_all("p")
                    user_name = p_tags[0].get_text(strip=True) if len(p_tags) > 0 else "Unknown"
                    age_gender = p_tags[1].get_text(strip=True) if len(p_tags) > 1 else "Unknown"
                else:
                    user_name = "Unknown"
                    age_gender = "Unknown"

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
                    usage_count = user_data_dict.get("利用人数", "Unknown")
                    date = user_data_dict.get("投稿日", "Unknown")
                    purpose = user_data_dict.get("利用目的", "Unknown")
                else:
                    usage_count = "Unknown"
                    date = "Unknown"
                    purpose = "Unknown"
            else:
                user_name = "Unknown"
                age_gender = "Unknown"
                usage_count = "Unknown"
                date = "Unknown"
                purpose = "Unknown"

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
                    overall_score = total_score_section.find("span", class_="review-totalscore").get_text(strip=True)
                else:
                    overall_score = "Unknown"

                # 各カテゴリーのスコア取得
                category_scores = score_section.find_all("dl", class_="review__list--box__score--categoryScore")
                scores = {}
                for category in category_scores:
                    dt = category.find("dt").get_text(strip=True)
                    dd = category.find("dd", class_="score").get_text(strip=True)
                    scores[dt] = dd
                plan_score = scores.get("プラン", "Unknown")
                atmosphere_score = scores.get("雰囲気", "Unknown")
                food_score = scores.get("料理", "Unknown")
                cost_performance_score = scores.get("コスパ", "Unknown")
                service_score = scores.get("サービス", "Unknown")
            else:
                overall_score = "Unknown"
                plan_score = "Unknown"
                atmosphere_score = "Unknown"
                food_score = "Unknown"
                cost_performance_score = "Unknown"
                service_score = "Unknown"

            # 利用プラン情報の取得
            plan_section = review_detail[1].find("div", class_="review__list--box__plan--text")
            if plan_section:
                plan_title_tag = plan_section.find("p", class_="review__list--box__plan--title")
                plan_menu_tag = plan_section.find("p", class_="review__list--box__plan--menu")
                plan_menu = plan_menu_tag.get_text(strip=True) if plan_menu_tag else "Unknown"
            else:
                plan_menu = "Unknown"

            # コメントの取得
            comments = review_detail[1].find_all("dl", class_="review__list--box__comment")
            comment_food_drink = "Unknown"
            comment_atmosphere_service = "Unknown"
            comment_reactions = "Unknown"
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
                    "user_name": user_name,
                    "age_gender": age_gender,
                    "usage_count": usage_count,
                    "date": date,
                    "purpose": purpose,
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

        # サーバーへの負荷を避けるために待機
        time.sleep(1)

    except Exception as e:
        print(f"Error processing {url}: {e}")
        exit()

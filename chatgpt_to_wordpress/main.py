import base64
import praw
from models import Trend, session
from typing import Any, Dict, List, Union
from config import my_client_id, my_client_secret, my_user_agent, my_refresh_token, openapi_key, application_password, api_base_url, username
from typing import Optional
import openai
openai.api_key = openapi_key
from sqlalchemy import and_
import json
import requests
AuthHeader = Dict[str, str]
PostData = Dict[str, Union[str, Any]]
APIResponse = Union[Dict[str, Any], None]


def get_all_trends_in_db() -> List[str]:
    """
    Retrieve a list of all trend names from the database.

    Args:
        session: A SQLAlchemy session object.

    Returns:
        A list of strings representing the names of all trends in the database.
    """
    with session.begin_nested():
        all_trends: List[Trend] = session.query(Trend)
        all_trends_list: List[str] = []
        for trend in all_trends:
            all_trends_list.append(trend.trend_name)
    return all_trends_list


def process_reddit_trends_01(num_trends:int=1) -> None:
    """
    Process the latest trends from the ChatGPT subreddit on Reddit and add them to the database.

    Args:
        session: A SQLAlchemy session object.
        num_trends: The number of latest trends to process (default: 1).

    Returns:
        None.
    """
    reddit: praw.Reddit = praw.Reddit(
        client_id=my_client_id,
        client_secret=my_client_secret,
        user_agent=my_user_agent,
        refresh_token=my_refresh_token,
    )

    ChatGPT: praw.models.Subreddit = reddit.subreddit('ChatGPT')
    hot_ChatGPT: List[praw.models.Submission] = list(ChatGPT.new(limit=num_trends))

    with session.begin_nested():
        for submission in hot_ChatGPT:
            if submission.title not in get_all_trends_in_db():
                session.add(Trend(trend_name=submission.title))
                print(f"Added {submission.title} to the database.")
                session.commit()
            else:
                print(f"{submission.title} already exists in the database.")

    return None


def generate_article_title(keyword: str) -> Optional[str]:
    """
    Generates a title for an article about the given keyword using OpenAI's GPT-3 API.

    Args:
        keyword (str): The keyword to generate a title for.

    Returns:
        Optional[str]: The generated title, or None if no title was generated.
    """
    prompt: str = f"Generate a title for an article about {keyword}."
    response: openai.Completion = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=30,
        n=1,
        stop=None,
        temperature=0.7,
    )
    only_choice = response.choices[0].text.strip()
    return only_choice if only_choice else None


def process_article_title_trends_02() -> None:
    """
    Generate article titles for trends that don't have a title yet.

    This function queries the database for trends that have a `trend_name` but no `title`,
    generates an article title for each trend using the `generate_article_title` function,
    and updates the `title` attribute of each trend with the generated title.

    Returns:
        None.
    """
    with session.begin_nested():
        trends: List[Trend] = session.query(Trend).filter(
            and_(Trend.trend_name.isnot(None), Trend.title.is_(None))).limit(1).all()

        titles: List[str] = [generate_article_title(trend.trend_name) for trend in trends]

        for trend, title in zip(trends, titles):
            title: str = generate_article_title(trend.trend_name)
            trend.title = title


def create_article(title: str, content: str, status: str = "draft") -> Optional[Dict[str, Any]]:
    """
    Creates a new article in WordPress with the given title and content.

    Args:
        title (str): The title of the article.
        content (str): The content of the article.
        status (str, optional): The status of the article. Defaults to "draft".

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing information about the created article, or None if the article was not created.
    """
    auth_header: AuthHeader = {}
    auth_header["Authorization"] = f"Basic {base64.b64encode((username + ':' + application_password).encode()).decode()}"

    post_data: PostData = {
        "title": title,
        "content": content,
        "status": status
    }

    response: APIResponse = requests.post(f"{api_base_url}posts", headers=auth_header, json=post_data)

    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating article: {response.json()}")
        return None

def process_article_creation_03() -> None:
    """
    Create articles for trends that have a title but no article.

    This function queries the database for trends that have a `trend_name` and `title` but no `article_id`,
    creates an article for each trend using the `create_article` function,
    and updates the `article_id` attribute of each trend with the ID of the created article.

    Returns:
        None.
    """
    with session.begin_nested():
        trends: List[Trend] = session.query(Trend).filter(Trend.article_id.is_(None), Trend.title.isnot(None)).all()
        [create_article(trend.title.replace('"', ''), "This is a test article.")["id"] for trend in trends if create_article(trend.title.replace('"', ''), "This is a test article.")]
        session.commit()

if __name__ == '__main__':
    process_reddit_trends_01()
    process_article_title_trends_02()
    process_article_creation_03()
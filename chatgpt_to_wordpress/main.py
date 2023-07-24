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


from datetime import datetime

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
                session.add(Trend(trend_name=submission.title, timestamp=f"{datetime.now()}:process_reddit_trends_01"))
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
            trend.timestamp = f"{datetime.now()}:process_article_title_trends_02"


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
        for trend in trends:
            try:
                title: str = trend.title.replace('"', '')
                article: Optional[Dict[str, Any]] = create_article(title, "This is a test article.")
                trend.article_id: Optional[int] = article["id"] if article else None
                trend.timestamp = f"{datetime.now()}:process_article_creation_03"
                session.add(trend)
            except Exception as e:
                print(e)
                pass

def generate_article_content(keyword: str) -> Optional[str]:
    """
    Generates an article content with 4 paragraphs about the given keyword with a call to action.

    Args:
        keyword (str): The keyword to generate the article about.

    Returns:
        Optional[str]: The generated article content, or None if the generation failed.
    """
    prompt: str = f"Generate an article with 4 paragraphs about {keyword} with a call to action."
    response: openai.Response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7,
    )
    only_choice: str = response.choices[0].text.strip()
    return only_choice if only_choice else None

def process_article_content_generation_04() -> None:
    """
    Generates article content for all trends that have a title but no article content.

    This function queries the database for trends that have a `trend_name` and `title` but no `article`,
    generates article content for each trend using the `generate_article_content` function,
    and updates the `article` attribute of each trend with the generated content.

    Returns:
        None.
    """
    with session.begin_nested():
        all_trends: List[Trend] = session.query(Trend).filter(and_(Trend.title.isnot(None), Trend.article.is_(None))).all()
        for trend in all_trends:
            try:
                article: Optional[str] = generate_article_content(trend.title)
                trend.article = article
                trend.timestamp = f"{datetime.now()}:process_article_content_generation_04"
            except Exception as e:
                print(e)
                pass

def update_article(postId: int, content: str, title: str, status: str = "draft") -> Optional[Dict[str, Any]]:
    """
    Updates an existing article on a WordPress site.

    Args:
        postId (int): The ID of the post to update.
        content (str): The new content of the post.
        title (str): The new title of the post.
        status (str, optional): The new status of the post. Defaults to "draft".

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the updated post data, or None if the update failed.
    """
    with open('config.json', 'r') as config_file:
        keys: dict = json.load(config_file)
        username: str = keys["username"]
        api_base_url: str = keys["api_base_url"]
        application_password: str = keys["application_password"]

    auth_header: str = f"{username}:{application_password}"
    auth_header = base64.b64encode(auth_header.encode("utf-8")).decode("utf-8")
    headers: Dict[str, str] = {"Authorization": f"Basic {auth_header}"}

    post_data: Dict[str, Any] = {
        "title": title,
        "content": content,
        "status": status,
        "categories": [373]
    }

    response: requests.Response = requests.post(f"{api_base_url}posts/{postId}", headers=headers, json=post_data)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(response.status_code)
        print(f"Error editing article: {response.json()}")
        return None

def process_article_update_05() -> None:
    """
    Updates all articles in the database that have not been published yet.

    This function retrieves all trends from the database that have an associated article ID but have not been updated on WordPress yet. It then updates each article on WordPress with the corresponding content and title from the trend. If the update is successful, the `article_wordpress_updated` field for the trend is set to True in the database.

    Returns:
        None
    """
    with session.begin_nested():
        all_trends: List[Trend] = session.query(Trend).filter(Trend.article_wordpress_updated.is_(None), Trend.article_id.isnot(None)).all()
        for trend in all_trends:
            try:
                trend.title = trend.title.replace('"', '')
                update_article(postId=trend.article_id, content=trend.article, title=trend.title)
                trend.article_wordpress_updated = True
                trend.timestamp = f"{datetime.now()}:process_article_update_05"
            except Exception as e:
                print(e)

def generate_article_tags(keyword: str) -> Optional[str]:
    """
    Generates ten tags for an article about the given keyword using OpenAI's GPT-3 API.

    Args:
        keyword (str): The keyword to generate tags for.

    Returns:
        Optional[str]: A string of comma-separated tags without hashes, or None if no tags were generated.
    """
    prompt: str = f"Write ten tags for an article about this topic [{keyword}]. Create comma separated tags without hashes."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.7,
    )
    only_choice: str = response.choices[0].text.strip()
    return only_choice if only_choice else None

def process_article_tags_generation_06() -> None:
    """
    Generates tags for all articles in the database that have not been tagged yet.

    This function retrieves all trends from the database that have an associated article but have not been tagged yet. It then generates tags for each article using OpenAI's GPT-3 API and saves the tags to the database.

    Returns:
        None
    """
    with session.begin_nested():
        all_trends = session.query(Trend).filter(and_(Trend.article != '', Trend.article_tags.is_(None)))
        for trend in all_trends:
            try:
                tags: Optional[str] = generate_article_tags(keyword=trend.title)
                trend.article_tags = tags
                trend.timestamp = f"{datetime.now()}:process_article_tags_generation_06"
            except Exception as e:
                print(e)
                session.rollback()

    return None

if __name__ == '__main__':
    process_reddit_trends_01()
    process_article_title_trends_02()
    process_article_creation_03()
    process_article_content_generation_04()
    process_article_update_05()
    process_article_tags_generation_06()
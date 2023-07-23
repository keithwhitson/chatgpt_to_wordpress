import praw
from models import Trend, session
from typing import List
from config import my_client_id, my_client_secret, my_user_agent, my_refresh_token

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

print(get_all_trends_in_db())
process_reddit_trends_01()
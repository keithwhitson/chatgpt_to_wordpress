import base64
import praw
from models import Trend, session
from typing import Any, Dict, List, NoReturn, Union
from config import my_client_id, my_client_secret, my_user_agent, my_refresh_token, openapi_key, application_password, api_base_url, username, tags_url, auth_header
from typing import Optional
import openai
openai.api_key = openapi_key
from sqlalchemy import and_
import os
import requests
AuthHeader = Dict[str, str]
PostData = Dict[str, Union[str, Any]]
APIResponse = Union[Dict[str, Any], None]
from stable_diffusion_tf.stable_diffusion import StableDiffusion
from PIL import Image


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

def get_tags() -> Dict[str, int]:
    """
    Retrieves all current tags from the WordPress site and returns them as a dictionary with tag names as keys and tag IDs as values.

    Returns:
        Dict[str, int]: A dictionary with tag names as keys and tag IDs as values.
    """
    all_current_tags_with_ids: Dict[str, int] = {}
    params: Dict[str, int] = {'per_page': 10}
    response = requests.get(tags_url, params=params)
    total_tags: int = int(response.headers.get('X-WP-Total'))
    tags_per_page: int = 10
    total_pages: int = int(response.headers.get('X-WP-TotalPages'))
    print(f'Total number of tags: {total_tags}')
    print(f'Tags per page: {tags_per_page}')
    print(f'Total number of pages: {total_pages}')

    for page in range(1, total_pages + 1):
        params = {'per_page': 10, 'page': page}
        response = requests.get(tags_url, params=params)
        tags = response.json()
        for tag in tags:
            all_current_tags_with_ids[tag['name']] = tag['id']
    return all_current_tags_with_ids

def tags_on_wordpress_check_and_update(tags_from_article: List[str]) -> None:
    """
    Checks if tags from an article already exist on the WordPress site and creates new tags if necessary.

    This function takes a list of tags from an article and checks if each tag already exists on the WordPress site. If a tag does not exist, it creates a new tag using the WordPress API.

    Args:
        tags_from_article (List[str]): A list of tags from an article.

    Returns:
        None
    """
    current_tags = get_tags()
    for tag in tags_from_article:
        print(tag.strip())
        try:
            print(f'Current Tag: {tag}')
            current_tags[tag.strip()]
        except:
            print(f'New tag: {tag}')
            post_data: Dict[str, str] = {'name': tag.strip()}

            headers: Dict[str, str] = {"Authorization": f"Basic {auth_header}"}
            response = requests.post(f"{api_base_url}tags", headers=headers, json=post_data)
            print(f"Response: {response.status_code}")
            print(response.json())

    return None

def add_tags_to_article(tags_array: List[int], article_id: int) -> None:
    print(article_id)
    print(tags_array)
    tags: List[Dict[str, int]] = []
    for tag in tags_array:
        tags.append({'id': tag})
    print(tags)
    url: str = f"https://www.blacktwitter.eu/wp-json/wp/v2/posts/{article_id}"
    t_: Dict[str, List[Dict[str, int]]] = {'tags': tags}
    t_['name'] = 'newtag'
    print(t_)
    headers: Dict[str, str] = {"Authorization": f"Basic {auth_header}"}
    response = requests.post(url, headers=headers, json=t_)
    print(f"Response: {response.status_code}")
    print(response.json())

def ensure_all_tags_exist() -> None:
    with session.begin_nested():
        trends = session.query(Trend).filter(and_(Trend.article_id != None, Trend.article != '', Trend.article_tags.is_(None))).all()
        for trend in trends:
            try:
                tags = trend.article_tags.split(',')
                tags_on_wordpress_check_and_update(tags)
            except Exception as e:
                print(e)
                pass

def process_article_tags_07() -> None:
    """
    Processes article tags for all trends in the database that have article tags but no tags added to the article yet.
    Retrieves all tags from the database and loops through all trends to find tags that match.
    If a tag is found, it is added to the list of found tags. If not, it is added to the list of not found tags.
    The list of found tags is then added to the article using the WordPress API.
    """

    with session.begin_nested():
        all_trends = session.query(Trend).filter(and_(Trend.article_tags.isnot(None), Trend.article_tags_added.is_(None))).all()
        for trend in all_trends:
            tags = get_tags()
            ensure_all_tags_exist()
            found_tags: List[int] = []
            not_found_tags: List[str] = []
            for tag in trend.article_tags.split(','):
                try:
                    tag_ = tag.strip()
                    found_tags.append(tags[tag_])
                except Exception as e:
                    not_found_tags.append(tag_)
                    print(e)
            postData: Dict[str, List[int]] = {}
            postData['tags'] = found_tags
            headers: Dict[str, str] = {"Authorization": f"Basic {auth_header}"}
            try:
                response = requests.post(f"{api_base_url}posts/{trend.article_id}", headers=headers, json=postData)
                trend.article_tags_added = True
                trend.timestamp = f"{datetime.now()}:process_article_tags_07"
            except Exception as e:
                print(e)
                print(f"Error: {trend.article_id}")
                pass
            print(f"Status Code: {response.status_code}")

def process_article_excerpts_08() -> None:
    """
    Generates a two sentence synopsis of each article in the database that has a title, article_id, article, article_excerpt, article_tags, and article_status.
    Uses OpenAI's text-davinci-003 engine to generate the synopsis.
    The generated synopsis is then added to the article_excerpt field in the database.
    """

    with session.begin_nested():
        all_trends: List[Trend] = session.query(Trend).filter(and_(
            Trend.title.isnot(None),
            Trend.article_excerpt.is_(None),
        ))

        for idx, trend in enumerate(all_trends):
            print(f"{idx} - {trend.title}")
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=f"Write a two sentence synopsis of [{trend.title}].",
                    max_tokens=50,
                    n=1,
                    stop=None,
                    temperature=0.7
                )
                only_choice: str = response.choices[0].text.strip()
                trend.article_excerpt = only_choice
            except Exception as e:
                print(e)
                break

def process_article_excerpt_09() -> None:
    """
    Updates the excerpt of all articles in the database that have an excerpt but have not been published yet.
    Uses the WordPress REST API to update the excerpt of each article.
    """

    def update_excerpt(excerpt: str) -> None:
        headers: dict = {"Authorization": f"Basic {auth_header}"}
        postData: dict = {"excerpt": excerpt}
        response: requests.Response = requests.post(f"{api_base_url}posts/{trend.article_id}", headers=headers, data=postData)
        print(response)
        print(f"Response: {response.status_code}")
        print(response.status_code)
        print(excerpt)

    with session.begin_nested():
        all_trends = session.query(Trend).filter(and_(
            Trend.article_excerpt.isnot(None),Trend.article_excerpt_added.is_(None)
        ))

        for trend in all_trends:
            try:
                update_excerpt(trend.article_excerpt)
                trend.article_excerpt_added = True
            except Exception as e:
                print(e)

generator = StableDiffusion(
    img_height=512,
    img_width=512,
    jit_compile=False,
)

def generate_image(prompt: str, filename:str) -> None:
    """
    Generates an image based on the given prompt using the StableDiffusion model.
    Saves the generated image to the specified filename.

    Args:
        prompt (str): The prompt to generate the image from.
        filename (str): The filename to save the generated image to.

    Returns:
        None
    """
    img = generator.generate(
        prompt,
        num_steps=5,
        unconditional_guidance_scale=2,
        temperature=1,
        batch_size=2,
    )
    Image.fromarray(img[0]).save(f"{filename}")

def process_trends_10() -> None:
    """
    Processes all trends that have an article_id, article, article_tags, no article_image_location, and article_status is not published.
    Generates an image based on the trend's title using the StableDiffusion model and saves it to the specified filename.
    Updates the trend's article_image_location with the filename.
    """
    with session.begin_nested():
        all_trends: List[Trend] = session.query(Trend).filter(and_(
            Trend.article_id != None,
            Trend.article != '',
            Trend.article_tags != None,
            Trend.article_image_location.is_(None),
            Trend.article_status.isnot('published')
        )).all()


        for trend in all_trends:
            try:
                filename: str = f"images/{trend.article_id}.png"
                if not os.path.exists(filename):
                    generate_image(trend.title, filename)
                trend.article_image_location: Optional[str] = filename
                session.add(trend)
            except Exception as e:
                print(e)

def process_update_trends_11() -> NoReturn:
    """
    Updates all trends that have an article_id, article, article_tags, article_image_location, and article_status is not published.
    Uploads the trend's article_image_location to the WordPress media library and updates the trend's article_image_id with the uploaded image's ID.
    Updates the trend's article_status to "published" and updates the trend's article_link with the link to the published article.

    Returns:
        None
    """
    with session.begin_nested():

        all_trends = session.query(Trend).filter(and_(Trend.article_id != None,\
            Trend.article != '', Trend.article_tags != None, \
            Trend.article_image_location !=None,
            Trend.article_status.isnot('published'),
            Trend.article_status == None)).all()

        for trend in all_trends:
            try:
                img_filename: str = trend.article_image_location
                media_url: str = f"{api_base_url}media"
                auth_header: str = f"{username}:{application_password}"
                auth_header = base64.b64encode(auth_header.encode("utf-8")).decode("utf-8")
                img_file: bytes = open(f"{img_filename}", "rb").read()
                media_headers = {
                    "Authorization": f"Basic {auth_header}",'Content-Type': 'image/png','Content-Disposition' : f"attachment; filename={img_filename}"
                }
                media_response = requests.post(media_url, headers=media_headers, data=img_file)
                image_id: int = media_response.json()["id"]
                trend.article_image_id = image_id
                post_url: str = f"{api_base_url}posts/{trend.article_id}"
                post_data = {
                    "featured_media": image_id,
                    "status": "publish"
                }
                auth_header = f"{username}:{application_password}"
                auth_header = base64.b64encode(auth_header.encode("utf-8")).decode("utf-8")
                post_headers = {
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/json"
                }
                post_response = requests.put(post_url, json=post_data, headers=post_headers)
                post_link: str = post_response.json().get("link","")
                trend.article_link = post_link
                print(post_response.status_code)
                print(f"Link: {post_response.json().get('link','')}")
                print(trend.title)
                trend.article_status = "published"
                print(media_response.status_code)
                session.add(trend)

            except Exception as e:
                print(str(e))
                print("error")
                pass



if __name__ == '__main__':
    process_reddit_trends_01()
    process_article_title_trends_02()
    process_article_creation_03()
    process_article_content_generation_04()
    process_article_update_05()
    process_article_tags_generation_06()
    process_article_tags_07()
    process_article_excerpts_08()
    process_article_excerpt_09()
    process_trends_10()
    process_update_trends_11()

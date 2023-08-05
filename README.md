# chatgpt_to_wordpress

This powerful tool uses AI to automate the process of content creation for your WordPress blog. It harnesses the intelligence of ChatGPT to not only fetch the latest trends from a subreddit (in this case 'ChatGPT'), but also to generate compelling article titles, create initial article drafts, produce engaging full article content, and even create suitable tags for each article. In addition, it uses the StableDiffusion model to generate images related to the article topics.

The tool provides a streamlined workflow by automating these often time-consuming tasks, allowing you to focus more on refining your ideas and adding the personal touch to your articles.

The example website used to demonstrate the tool's capabilities is [BlackTwitter.eu](https://www.blacktwitter.eu/). However, the tool is designed to work with any WordPress website.

## Prerequisites

To use this tool, you need to have the following:

- Reddit credentials for fetching trends from the subreddit 'ChatGPT'
- OpenAI credentials for using the GPT-3 engine
- WordPress credentials for creating and updating articles on your WordPress site

## Setup

1. **Create a Config File**: In order to make this work, you need to create a `config.json` file which contains the following information:

```json
{
    "client_id": "your_reddit_client_id",
    "client_secret": "your_reddit_client_secret",
    "user_agent": "your_reddit_user_agent",
    "refresh_token": "your_reddit_refresh_token",
    "openapi_key":"your_openai_api_key",
    "username" : "your_wordpress_username",
    "api_base_url" : "https://www.xxx.eu/wp-json/wp/v2/",
    "application_password" : "your_wordpress_application_password",
    "tags_url":"https://www.xxx.eu/wp-json/wp/v2/tags",
    "cloudinary_cloud_name" : "your_cloudinary_cloud_name",
    "cloudinary_api_key" : "your_cloudinary_api_key",
    "cloudinary_api_secret" : "your_cloudinary_api_secret",
    "cloudinary_secure" : "True_or_False",
    "aritable_api_key" : "your_airtable_api_key",
    "aritable_base_id":"your_airtable_base_id",
    "aritable_table_name":"your_airtable_table_name"
}
```

Replace each "your_" placeholder with your actual credentials.

2. **Install Required Packages**: Ensure you have all required Python packages installed. You can do this with Poetry by running `poetry install` in the directory where your `pyproject.toml` file is located.

3. **Run the Tool**: Here's how to run the tool using Poetry:

   - Open Terminal or Command Prompt and navigate to the directory where your `main.py` script and `pyproject.toml` file are located.
   - If you haven't installed Poetry yet, you can do so by following the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
   - To install all dependencies, run `poetry install`.
   - To activate the virtual environment created by Poetry, run `poetry shell`.
   - Finally, run your Python script using `python main.py`.

This tool aims to enhance your content creation process, freeing up your time and energy to focus on what matters most: creating engaging and meaningful content for your audience.

## Note

Please remember that while AI can generate engaging content, it is always a good idea to review and edit the generated content to ensure it aligns with your style, voice, and the message you wish to convey to your audience.
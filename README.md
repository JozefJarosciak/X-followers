
# X.com (Twitter) Follower Data Extractor

`x-followers.py` is a Python script that extracts follower data from a specified X.com handle and displays the top followers based on their popularity (follower count). 
Script also provides options to use cached data or fetch new data from X.com's API, with progress tracking and retry handling for API rate limits.

## Features

- Fetches and saves follower IDs and details for a specified X.com handle.
- Progress tracking of data retrieval with percentage completion.
- Displays top followers sorted by follower count.
- Caches data to minimize redundant API calls.
- Customizable settings for data caching, number of top followers, and output format.

## Requirements

- Python 3.6+
- X.com API Bearer Token

## Getting an X.com API Bearer Token

To use this script, you'll need an X.com API Bearer Token. Follow these steps to obtain one:

1. **Apply for an X.com Developer Account**:
   - Visit the [X Developer website](https://developer.twitter.com/en) and apply for a developer account if you don't already have one.

2. **Create a New Project and App**:
   - Log in to the X.com Developer portal after your account is approved.
   - Navigate to the **Projects & Apps** section and create a new project and app. 
   - This will generate API keys and tokens specific to your app.

3. **Generate the Bearer Token**:
   - Go to the **Keys and Tokens** tab in your app's settings.
   - Under **Bearer Token**, click **Generate** (or **Regenerate** if you already have one). Copy the token.

4. **Add the Bearer Token to the Script**:
   - In `x-followers.py`, paste your Bearer Token in the `bearer_token` variable:

     ```python
     bearer_token = "YOUR_BEARER_TOKEN_HERE"
     ```

   This token allows the script to authenticate with the X.com API and access follower information.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JozefJarosciak/X-followers.git
   cd X-followers
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your X.com API Bearer Token in the script.

## Usage

1. **Configure the Script**: Open `x-followers.py` and add your X.com API Bearer Token and desired X.com handle. The relevant configuration variables are:

   ```python
   bearer_token = "<your_bearer_token>"
   handle = "<x.com_handle>"  # Example: "xenpub" (without the @ sign)
   ```

2. **Run the Script**:
   ```bash
   python x-followers.py
   ```

3. **Output**: The script will display the progress of data collection, save data to a CSV file, and display the top followers sorted by follower count.

Example output:

![image](https://github.com/user-attachments/assets/233d5191-44a3-4476-8568-c6ce4b1ecc74)

   

## Script Structure

- `get_follower_count(handle)`: Retrieves the total follower count for the specified handle.
- `get_all_follower_ids(handle, existing_ids)`: Retrieves all follower IDs for the specified handle, filtering out existing ones.
- `load_existing_user_ids(filename)`: Loads cached user IDs from an existing CSV file to avoid reprocessing.
- `get_user_details(ids_list, filename)`: Fetches and saves user details for the provided follower IDs.
- `display_top_followers(filename, top_n)`: Sorts and displays the top followers based on follower count.

## Notes

- **Rate Limits**: The script includes handling X.com API rate limits with automatic retries.
- **Cache Control**: Set `use_existing_data_only` to `True` to avoid fetching new data if existing data is available.
- **Sorting and Columns**: Customize the `output_columns` dictionary to adjust displayed columns and sorting preferences.

## License

This project is licensed under the MIT License.

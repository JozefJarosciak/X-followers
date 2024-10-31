
# X.com (Twitter) Follower Data Extractor

`x-followers.py` is a Python script that extracts follower data from a specified X.com handle and displays the top followers based on follower count. It provides options to use cached data or fetch new data from X.com's API, with progress tracking and retry handling for API rate limits.

## Features

- Fetches and saves follower IDs and details for a specified X.com handle.
- Shows the progress of data retrieval with percentage completion.
- Sorts and displays top followers based on follower count.
- Caches data to avoid redundant API calls.
- Configurable options for data caching, number of top followers, and output format.

## Requirements

- Python 3.6+
- X.com API Bearer Token

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JozefJarosciak/X-followers.git
   cd X-followers


2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your X.com API Bearer Token in the script.

## Usage

1. **Configure the Script**: Open `x-followers.py` and add your X.com API Bearer Token and desired X.com handle. The relevant configuration variables are:

   ```python
   bearer_token = "<your_bearer_token>"
   handle = "<x.com_handle>"  # Example: "ackebom" (without the @ sign)
   ```

2. **Run the Script**:
   ```bash
   python x-followers.py
   ```

3. **Output**: The script will display the progress of data collection, save data to a CSV file, and display the top followers sorted by follower count.

Screenshot example:
   ![image](https://github.com/user-attachments/assets/2ee45e38-7746-4086-86d8-e1e887b864ae)


## Script Structure

- `get_all_follower_ids(handle)`: Retrieves all follower IDs for the specified handle.
- `load_existing_user_ids(filename)`: Loads cached user IDs from an existing CSV file.
- `get_user_details(ids_list, filename)`: Fetches and saves user details for the provided follower IDs.
- `display_top_followers(filename, top_n)`: Sorts and displays the top followers based on follower count.

## Notes

- **Rate Limits**: The script includes handling X.com API rate limits with automatic retries.
- **Cache Control**: Set `use_existing_data_only` to `True` to avoid fetching new data if existing data is available.
- **Sorting and Columns**: Customize the `output_columns` dictionary to adjust displayed columns and sorting preferences.

## License

This project is licensed under the MIT License.

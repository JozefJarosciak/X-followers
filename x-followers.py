import requests
import time
import os
from datetime import datetime
import pandas as pd
from tabulate import tabulate

# === Configuration Section ===
bearer_token = ""  # X.com API Bearer Token
handle = ""  # X.com handle to analyze (do not include the @ sign). E.g. "xenpub"
top_n = 20  # Number of top followers to display
use_existing_data_only = True  # If True, use existing data without fetching new

# Output columns configuration for the top followers display
output_columns = {
    'screen_name': {'label': 'Screen Name'},
    'followers_count': {'label': 'Followers Count', 'sort': True},
    'joined': {'label': 'Joined X.com'},
    'name': {'label': 'Name'}
}

# === API Endpoints ===
ENDPOINT_FOLLOWERS_IDS = "https://api.X.com.com/1.1/followers/ids.json"
ENDPOINT_USERS_LOOKUP = "https://api.X.com.com/1.1/users/lookup.json"
ENDPOINT_USER_SHOW = "https://api.X.com.com/1.1/users/show.json"

# === Headers Setup ===
headers = {
    "Authorization": f"Bearer {bearer_token}"
}

# === Function Definitions ===

def get_follower_count(handle):
    """
    Retrieve the total follower count for the specified X.com handle.

    Args:
        handle (str): X.com handle to fetch follower count for.

    Returns:
        int: Total number of followers for the handle.
    """
    response = requests.get(ENDPOINT_USER_SHOW, headers=headers, params={"screen_name": handle})
    if response.status_code == 200:
        data = response.json()
        return data.get("followers_count", 0)
    else:
        raise Exception(f"Error fetching follower count: {response.status_code} - {response.text}")

def get_all_follower_ids(handle, existing_ids):
    """
    Retrieve all follower IDs for a given X.com handle, filtering out existing ones.

    Args:
        handle (str): X.com handle to fetch followers for.
        existing_ids (set): Set of IDs already processed to avoid re-fetching.

    Returns:
        list: List of new follower IDs not in existing_ids.
    """
    total_followers = get_follower_count(handle)  # Get estimated total followers count
    follower_ids = []
    next_cursor = -1
    session = requests.Session()
    total_retrieved = 0
    skipped_ids = 0  # Track how many IDs were skipped

    print(f"Starting follower ID retrieval for @{handle}. Estimated total followers: {total_followers}")

    # Loop through paginated requests until all followers are retrieved
    while True:
        params = {"screen_name": handle, "cursor": next_cursor, "count": 5000}
        response = session.get(ENDPOINT_FOLLOWERS_IDS, headers=headers, params=params)

        # Handle rate limits
        if response.status_code == 429:
            reset_time = int(response.headers.get('x-rate-limit-reset', time.time() + 60))
            current_time = int(time.time())
            sleep_duration = max(reset_time - current_time, 1)  # Calculate remaining time until reset
            print(f"\rRate limit hit. Sleeping for {sleep_duration} seconds...", end="")
            time.sleep(sleep_duration)
            continue
        elif response.status_code != 200:
            print(f"\nError encountered: {response.status_code} - {response.text}")
            raise Exception(f"Error: {response.status_code} - {response.text}")

        data = response.json()

        # Process and filter IDs as they are retrieved
        retrieved_ids = data.get('ids', [])
        new_ids = [id for id in retrieved_ids if str(id) not in existing_ids]
        skipped_ids += len(retrieved_ids) - len(new_ids)  # Track how many were skipped

        # Extend follower IDs list with new ones
        follower_ids.extend(new_ids)
        total_retrieved += len(new_ids)
        next_cursor = data.get('next_cursor', 0)

        # Display ongoing progress
        progress_percentage = min((total_retrieved / total_followers) * 100, 100)
        print(f"\rRetrieving follower IDs: {progress_percentage:.2f}% complete "
              f"({total_retrieved}/{total_followers}) - Skipped {skipped_ids} existing IDs", end="")

        # Break loop if there are no more pages
        if next_cursor == 0:
            break

    print("\nFollower ID retrieval complete. Total new IDs retrieved:", total_retrieved)
    return follower_ids




def load_existing_user_ids(filename):
    """
    Load existing user IDs from the CSV file to avoid reprocessing.

    Args:
        filename (str): Path to the CSV file.

    Returns:
        set: Set of existing user IDs as strings.
    """
    if os.path.exists(filename):
        return set(pd.read_csv(filename)['id'].astype(str))
    return set()

def get_user_details(ids_list, filename, retries=3, delay=5):
    """
    Fetch user details for a list of follower IDs and continuously update the CSV file.

    Args:
        ids_list (list): List of follower IDs.
        filename (str): Path to the CSV file.
        retries (int): Number of retry attempts for connection errors.
        delay (int): Delay in seconds between retry attempts.
    """
    existing_ids = load_existing_user_ids(filename)
    fieldnames = ['timestamp', 'id', 'screen_name', 'name', 'followers_count', 'created_at']
    session = requests.Session()

    total_ids = len(ids_list)  # Total number of IDs to process
    processed_ids = 0  # Counter to track progress

    # Prepare the CSV file for continuous writing
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            pd.DataFrame(columns=fieldnames).to_csv(f, index=False)

    for i in range(0, total_ids, 100):
        # Filter out already existing IDs
        ids_chunk = [str(id) for id in ids_list[i:i + 100] if str(id) not in existing_ids]
        if not ids_chunk:
            processed_ids += len(ids_chunk)
            continue

        # Retry loop for handling connection issues
        for attempt in range(retries):
            try:
                params = {"user_id": ",".join(ids_chunk)}
                response = session.get(ENDPOINT_USERS_LOOKUP, headers=headers, params=params)

                # Handle different HTTP responses
                if response.status_code == 404:
                    break
                elif response.status_code == 429:
                    reset_time = int(response.headers.get('x-rate-limit-reset', time.time() + 60))
                    time.sleep(max(reset_time - int(time.time()) + 1, 0))
                    continue
                elif response.status_code != 200:
                    raise Exception(f"Error: {response.status_code} - {response.text}")

                # Add new user data and write to file incrementally
                data = response.json()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_data = []
                for user in data:
                    user_data = {
                        'timestamp': timestamp,
                        'id': user['id_str'],
                        'screen_name': user['screen_name'],
                        'name': user['name'],
                        'followers_count': user['followers_count'],
                        'created_at': user.get('created_at', 'N/A')
                    }
                    new_data.append(user_data)
                    existing_ids.add(user['id_str'])

                # Continuously append new data to CSV file
                pd.DataFrame(new_data).to_csv(filename, mode='a', header=False, index=False)
                processed_ids += len(ids_chunk)
                break  # Exit retry loop if successful

            except requests.exceptions.ConnectionError as e:
                time.sleep(delay)
                continue  # Retry the loop

        # Calculate and display progress
        progress_percentage = (processed_ids / total_ids) * 100
        print(f"\rCollecting user details: {progress_percentage:.2f}% - Processed {processed_ids} of {total_ids} followers", end="")

    # Final newline after progress completion
    print("\nData collection complete.")

def display_top_followers(filename, top_n=50):
    """
    Display the top followers sorted by the specified column.

    Args:
        filename (str): Path to the CSV file.
        top_n (int): Number of top followers to display.
    """
    df = pd.read_csv(filename)

    # Determine selected columns and sorting
    selected_columns = {col: info['label'] for col, info in output_columns.items() if col in df.columns}
    sort_column = next((col for col, info in output_columns.items() if info.get('sort') and col in df.columns), None)

    if sort_column:
        df = df.sort_values(by=sort_column, ascending=False).reset_index(drop=True)
        sort_column_display = selected_columns[sort_column]
    else:
        sort_column_display = list(selected_columns.values())[0]

    # Filter and rename columns
    df = df[list(selected_columns.keys())].rename(columns=selected_columns)

    # Format dates and numbers
    if 'Joined X.com' in df.columns:
        df['Joined X.com'] = pd.to_datetime(df['Joined X.com'], errors='coerce').dt.strftime('%a %b %d, %Y').fillna('N/A')
    if 'Followers Count' in df.columns:
        df['Followers Count'] = pd.to_numeric(df['Followers Count'], errors='coerce').fillna(0).astype(int).apply(lambda x: f"{x:,}")

    # Display the top followers table
    top_followers = df.head(top_n)
    top_followers.index += 1

    # Set up color codes
    color_reset = "\033[0m"
    color_blue = "\033[94m"
    color_white = "\033[97m"
    color_bold = "\033[1m"

    # Define handle display with lines before and after
    handle_text = f"User: @{handle}"
    total_width = 50
    line = f"{color_blue}{color_bold}{'─' * total_width}{color_reset}"

    # Display user handle with colorized lines above and below
    handle_display = f"""{line}
{color_blue}{color_bold}──{color_reset}{color_white}{handle_text.center(total_width - 4)}{color_reset}{color_blue}{color_bold}──{color_reset}
{line}"""

    print(handle_display)
    print(f"Top {top_n} Accounts Following @{handle} (Ranked by {sort_column_display})")
    print(tabulate(top_followers, headers='keys', tablefmt='psql', showindex=True))

# === Main Execution ===

def main():
    filename = f"{handle}_followers.csv"
    existing_ids = load_existing_user_ids(filename)  # Load IDs that were already processed

    if use_existing_data_only:
        if os.path.exists(filename):
            print(f"Using existing file '{filename}' without fetching new data.")
        else:
            print(f"No existing file found. Fetching data for @{handle}...")
            follower_ids = get_all_follower_ids(handle, existing_ids)
            get_user_details(follower_ids, filename)
    else:
        print("Fetching all follower IDs...")
        follower_ids = get_all_follower_ids(handle, existing_ids)  # Fetch all follower IDs
        print("\nFiltering out already processed follower IDs...")

        # Filter out already existing IDs with progress display
        remaining_ids = []
        for index, id in enumerate(follower_ids):
            if str(id) not in existing_ids:
                remaining_ids.append(id)
            # Display progress for filtering
            progress_percentage = (index + 1) / len(follower_ids) * 100
            print(f"\rFiltering follower IDs: {progress_percentage:.2f}% complete", end="")

        print("\nFiltering complete.")

        if remaining_ids:
            get_user_details(remaining_ids, filename)



    display_top_followers(filename, top_n=top_n)


if __name__ == "__main__":
    main()

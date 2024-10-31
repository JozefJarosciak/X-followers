import requests
import time
import os
from datetime import datetime
import pandas as pd
from tabulate import tabulate

# === Configuration Section ===
bearer_token = ""  # Twitter API Bearer Token
handle = ""  # Twitter handle to analyze (do not include the @ sign), e.g. "ackebom"
top_n = 20  # Number of top followers to display
use_existing_data_only = True  # If True, use existing data without fetching new

# Output columns configuration for the top followers display
output_columns = {
    'screen_name': {'label': 'Screen Name'},
    'followers_count': {'label': 'Followers Count', 'sort': True},
    'joined': {'label': 'Joined Twitter'},
    'name': {'label': 'Name'}
}

# === API Endpoints ===
ENDPOINT_FOLLOWERS_IDS = "https://api.twitter.com/1.1/followers/ids.json"
ENDPOINT_USERS_LOOKUP = "https://api.twitter.com/1.1/users/lookup.json"

# === Headers Setup ===
headers = {
    "Authorization": f"Bearer {bearer_token}"
}

# === Function Definitions ===

def get_all_follower_ids(handle):
    """
    Retrieve all follower IDs for a given Twitter handle.

    Args:
        handle (str): Twitter handle to fetch followers for.

    Returns:
        list: List of follower IDs.
    """
    follower_ids = []
    next_cursor = -1
    session = requests.Session()

    # Loop through paginated requests until all followers are retrieved
    while True:
        params = {"screen_name": handle, "cursor": next_cursor, "count": 5000}
        response = session.get(ENDPOINT_FOLLOWERS_IDS, headers=headers, params=params)

        # Handle rate limits
        if response.status_code == 429:
            reset_time = int(response.headers.get('x-rate-limit-reset', time.time() + 60))
            time.sleep(max(reset_time - int(time.time()) + 1, 0))
            continue
        elif response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")

        data = response.json()
        follower_ids.extend(data.get('ids', []))
        next_cursor = data.get('next_cursor', 0)

        # Break loop if there are no more pages
        if next_cursor == 0:
            break
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
    Fetch user details for a list of follower IDs and update the CSV file.

    Args:
        ids_list (list): List of follower IDs.
        filename (str): Path to the CSV file.
        retries (int): Number of retry attempts for connection errors.
        delay (int): Delay in seconds between retry attempts.
    """
    existing_ids = load_existing_user_ids(filename)
    fieldnames = ['timestamp', 'id', 'screen_name', 'name', 'followers_count', 'created_at']
    new_data = []
    session = requests.Session()

    total_ids = len(ids_list)  # Total number of IDs to process
    processed_ids = 0  # Counter to track progress

    for i in range(0, total_ids, 100):
        ids_chunk = [str(id) for id in ids_list[i:i + 100] if str(id) not in existing_ids]
        if not ids_chunk:
            processed_ids += len(ids_chunk)  # Update counter even if skipped
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

                # Add new user data
                data = response.json()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

                processed_ids += len(ids_chunk)
                break  # Exit retry loop if successful

            except requests.exceptions.ConnectionError as e:
                time.sleep(delay)
                continue  # Retry the loop

        # Calculate and display progress
        progress_percentage = (processed_ids / total_ids) * 100
        print(f"\rProgress: {progress_percentage:.2f}% - Processed {processed_ids} of {total_ids} followers", end="")

    # Final newline after progress completion
    print("\nData collection complete.")

    # Save or update CSV file with new data if any
    if new_data:
        if os.path.exists(filename):
            existing_data = pd.read_csv(filename)
            all_data = pd.concat([pd.DataFrame(new_data), existing_data], ignore_index=True)
        else:
            all_data = pd.DataFrame(new_data)
        all_data.to_csv(filename, index=False, columns=fieldnames)
        print("User details updated and written to the file.")
    else:
        print("No new user data to update.")


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
    if 'Joined Twitter' in df.columns:
        df['Joined Twitter'] = pd.to_datetime(df['Joined Twitter'], errors='coerce').dt.strftime('%a %b %d, %Y').fillna('N/A')
    if 'Followers Count' in df.columns:
        df['Followers Count'] = pd.to_numeric(df['Followers Count'], errors='coerce').fillna(0).astype(int).apply(lambda x: f"{x:,}")

    # Display the top followers table
    top_followers = df.head(top_n)
    top_followers.index += 1
    print(f"\nTop {top_n} Accounts Following @{handle}\n(Ranked by {sort_column_display})")
    print(tabulate(top_followers, headers='keys', tablefmt='psql', showindex=True))

# === Main Execution ===

def main():
    filename = f"{handle}_followers.csv"

    if use_existing_data_only:
        if os.path.exists(filename):
            print(f"Using existing file '{filename}' without fetching new data.")
        else:
            print(f"No existing file found. Fetching data for @{handle}...")
            follower_ids = get_all_follower_ids(handle)
            get_user_details(follower_ids, filename)
    else:
        follower_ids = get_all_follower_ids(handle)
        if os.path.exists(filename):
            existing_ids = load_existing_user_ids(filename)
            remaining_ids = [id for id in follower_ids if str(id) not in existing_ids]
            if remaining_ids:
                get_user_details(remaining_ids, filename)
        else:
            get_user_details(follower_ids, filename)

    display_top_followers(filename, top_n=top_n)

if __name__ == "__main__":
    main()

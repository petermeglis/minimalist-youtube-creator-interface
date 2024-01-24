# -*- coding: utf-8 -*-

import os
import re
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import httplib2
import time
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


scopes = ["https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtube.upload"]

DEFAULT_UPLOAD_DIR = "~/storage/shared/fs/media/upload"
DEFAULT_UPLOAD_TIME = "17:00:00Z"
DEFAULT_LOCATION = "Federal Territory of Kuala Lumpur"

def get_authenticated_service():
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "oauth_client_secret.json"
    credentials_file = "youtube_credentials.json"  # File to save the credentials

    credentials = None
    # Load saved credentials from a file if it exists
    if os.path.exists(credentials_file):
        credentials = Credentials.from_authorized_user_file(credentials_file, scopes)
        print("Welcome back, Peter!")

    # If there are no valid credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
            credentials = flow.run_local_server()
        
        # Save the credentials for the next run
        with open(credentials_file, "w") as f:
            f.write(credentials.to_json())

    return googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)


def get_my_uploads_list(youtube):
    # Retrieve the contentDetails part of the channel resource for the authenticated user's channel.
    channels_response = youtube.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()

    for channel in channels_response["items"]:
        # From the API response, extract the playlist ID that identifies the list of videos uploaded to the authenticated user's channel.
        return channel["contentDetails"]["relatedPlaylists"]["uploads"]

def list_my_uploaded_videos(youtube, uploads_playlist_id, max_results=None):
    if max_results is None:
        max_results = input("Enter the number of videos to list (e.g., 10, 50, 75): ")
        try:
            max_results = int(max_results)
        except ValueError:
            print("Invalid number. Listing the default last 10 videos.")
            max_results = 10

    print(f"Last {max_results} videos in upload playlist:")

    playlistitems_list_request = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part="snippet",
        maxResults=max_results
    )

    playlistitems_list_response = playlistitems_list_request.execute()

    for playlist_item in playlistitems_list_response["items"]:
        title = playlist_item["snippet"]["title"]
        video_id = playlist_item["snippet"]["resourceId"]["videoId"]
        print(f"{title} (video ID: {video_id})")



# Helper function for duration response.
def parse_duration(duration):
    """Convert ISO 8601 duration to a more readable format."""
    match = re.match(r'P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    years, months, days, hours, minutes, seconds = [int(group) if group else 0 for group in match.groups()]
    
    readable_duration = ""
    if years:
        readable_duration += f"{years} years "
    if months:
        readable_duration += f"{months} months "
    if days:
        readable_duration += f"{days} days "
    if hours:
        readable_duration += f"{hours} hours "
    if minutes:
        readable_duration += f"{minutes} minutes "
    if seconds:
        readable_duration += f"{seconds} seconds "
    
    return readable_duration.strip()

def get_video(youtube):
    video_id = input("Enter the ID of the video to edit: ")

    # Retrieve current video details
    video_response = youtube.videos().list(
        part="snippet,contentDetails,status,recordingDetails",
        id=video_id
    ).execute()

    if not video_response["items"]:
        print("Video not found.")
        return

    video = video_response["items"][0]
    snippet = video["snippet"]
    content_details = video.get("contentDetails", {})
    status = video.get("status", {})
    recording_details = video.get("recordingDetails", {})
    thumbnail_url = snippet.get('thumbnails', {}).get('high', {}).get('url', 'N/A')

    # Display current details
    print(f"Title: {snippet.get('title', 'N/A')}")
    print(f"Duration: {parse_duration(content_details.get('duration', 'N/A'))}")

    print(f"Visibility: {status.get('privacyStatus', 'N/A')}")
    print(f"Upload date: {snippet.get('publishedAt', 'N/A')}")
    print(f"Scheduled for: {status.get('publishAt', 'N/A')}")

    print(f"Description: {snippet.get('description', 'N/A')}")
    print(f"Location: {recording_details.get('locationDescription', {})}")
    print(f"Thumbnail: {thumbnail_url}")

def edit_video(youtube):
    video_id = input("Enter the ID of the video to edit: ")

    # Retrieve current video details
    video_response = youtube.videos().list(
        part="snippet,contentDetails,status,recordingDetails",
        id=video_id
    ).execute()

    if not video_response["items"]:
        print("Video not found.")
        return

    video = video_response["items"][0]
    snippet = video["snippet"]
    content_details = video.get("contentDetails", {})
    status = video.get("status", {})
    recording_details = video.get("recordingDetails", {})
    thumbnail_url = snippet.get('thumbnails', {}).get('high', {}).get('url', 'N/A')

    # Display current details
    print(f"Title: {snippet.get('title', 'N/A')}")
    print(f"Duration: {parse_duration(content_details.get('duration', 'N/A'))}")

    print(f"Visibility: {status.get('privacyStatus', 'N/A')}")
    print(f"Upload date: {snippet.get('publishedAt', 'N/A')}")
    print(f"Scheduled for: {status.get('publishAt', 'N/A')}")

    print(f"Description: {snippet.get('description', 'N/A')}")
    print(f"Location: {recording_details.get('locationDescription', {})}")
    print(f"Thumbnail: {thumbnail_url}")

    print()

    # Ask for new details
    new_title = input("Enter new title (press enter to keep current): ")
    new_description = input("Enter new description (press enter to keep current): ")
    new_location = input("Enter new location description (press enter to keep current): ")

    new_scheduled_datetime = None

    # Handle scheduling
    if status.get('privacyStatus') == 'private':
        should_schedule = input("Video is private. Do you want to update the publish at time (y/n)? ").strip().lower()

        if should_schedule == 'y':
            # Default date is today's date
            default_date = datetime.now().strftime("%Y-%m-%d")
            scheduled_date = input(f"Enter the scheduled publish date (YYYY-MM-DD, default: {default_date} GMT): ")
            scheduled_date = scheduled_date or default_date

            default_time = DEFAULT_UPLOAD_TIME
            scheduled_time = input(f"Enter the scheduled publish time (hh:mm:ssZ, default: {default_time} GMT): ")
            scheduled_time = scheduled_time or default_time
            new_scheduled_datetime = f"{scheduled_date}T{scheduled_time}"

    thumbnail_path = input("Enter new thumbnail file path (press enter to keep current): ")


    print("Updating...")

    # Update details if provided
    if new_title:
        snippet["title"] = new_title
    if new_description:
        snippet["description"] = new_description
    if new_scheduled_datetime:
        status['publishAt'] = new_scheduled_datetime

    # Perform the update
    update_response = youtube.videos().update(
        part="snippet,status",
        body={
            "id": video_id,
            "snippet": snippet,
            "status": status
        }
    ).execute()

    # Update location if provided
    if new_location:
        recording_details = {"locationDescription": new_location}
    else:
        recording_details = None

    # Perform the update
    update_body = {
        "id": video_id,
        "snippet": snippet,
        "status": status
    }
    if recording_details:
        update_body["recordingDetails"] = recording_details

    update_response = youtube.videos().update(
        part="snippet,status,recordingDetails",
        body=update_body
    ).execute()

    # Update thumbnail if provided
    if thumbnail_path:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumbnail_path
        ).execute()

    print(f"Video updated: {update_response['snippet']['title']}")

def list_unreplied_comments(youtube):
    # Fetch the authenticated user's channel ID
    my_channel_response = youtube.channels().list(
        mine=True,
        part="id"
    ).execute()
    my_channel_id = my_channel_response["items"][0]["id"]

    video_id = input("Enter the ID of the video to check comments: ")

    try:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            author = top_comment["authorDisplayName"]
            comment_text = top_comment["textDisplay"]

            print(f"\nComment by {author}: {comment_text}")

            # Check if the comment has been replied to by your channel
            if "replies" in item:
                replies = item["replies"]["comments"]
                replied = any(reply["snippet"]["authorChannelId"]["value"] == my_channel_id for reply in replies)
                if not replied:
                    print(" - You have not replied to this comment.\n")
                else:
                    print(" - You have already replied to this comment.\n")
            else:
                print(" - You have not replied to this comment.\n")

    except googleapiclient.errors.HttpError as e:
        print(f"An error occurred: {e}")
        print("This may be due to disabled comments on the video.")


def list_videos_with_comment_count(youtube, uploads_playlist_id):
    max_results = input("Enter the number of videos to list with comment counts: ")
    try:
        max_results = int(max_results)
    except ValueError:
        print("Invalid number. Using the default of 10 videos.")
        max_results = 10

    print(f"Last {max_results} videos with comment counts:")

    # Retrieve the list of videos
    playlistitems_list_request = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part="snippet",
        maxResults=max_results
    )

    playlistitems_list_response = playlistitems_list_request.execute()

    for playlist_item in playlistitems_list_response["items"]:
        video_id = playlist_item["snippet"]["resourceId"]["videoId"]
        video_title = playlist_item["snippet"]["title"]

        # Retrieve video details including comment count
        video_request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        video_response = video_request.execute()

        comment_count = video_response["items"][0]["statistics"].get("commentCount", "N/A")

        print(f"Video Title: {video_title}, Video ID: {video_id}, Comment Count: {comment_count}")

def list_files_in_directory(directory):
    # List files and directories in the specified directory
    entries = os.listdir(directory)
    files = [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]
    directories = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]
    return files, directories

# Helper function: Create a custom progress indicator
def progress_callback(progress, chunk_size, total_size):
    percent_complete = progress.resumable_progress * 100
    print(f"Uploaded {int(percent_complete)}%")

def upload_video(youtube):
    # Use the default upload directory path
    upload_dir = os.path.expanduser(DEFAULT_UPLOAD_DIR)

    # List files and directories in the default directory
    files_in_dir, directories_in_dir = list_files_in_directory(upload_dir)

    if not files_in_dir:
        print("No files found in the default directory:", upload_dir)
        return

    print("Files available in the default directory:")
    for i, file_name in enumerate(files_in_dir, start=1):
        print(f"{i}. [File] {file_name}")
    for i, directory_name in enumerate(directories_in_dir, start=len(files_in_dir) + 1):
        print(f"{i}. [Directory] {directory_name}")

    # Ask the user if they want to upload from the default directory or enter a custom path
    while True:
        choice = input("Do you want to upload from the default directory (D) or enter a custom file path (C)? ").strip().lower()
        if choice == 'd':
            # User wants to upload from the default directory
            while True:
                try:
                    selected_index = int(input("Enter the index of the file you want to upload (1, 2, ...): "))
                    if 1 <= selected_index <= len(files_in_dir) + len(directories_in_dir):
                        if selected_index <= len(files_in_dir):
                            selected_item = os.path.join(upload_dir, files_in_dir[selected_index - 1])
                        else:
                            selected_item = os.path.join(upload_dir, directories_in_dir[selected_index - 1 - len(files_in_dir)])
                        break
                    else:
                        print("Invalid index. Please enter a valid index.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            break
        elif choice == 'c':
            # User wants to enter a custom file path
            custom_file_path = input("Enter the full path of the file you want to upload: ").strip()
            if os.path.isfile(custom_file_path):
                selected_item = custom_file_path
                break
            else:
                print("Invalid file path. Please enter a valid file path.")
        else:
            print("Invalid choice. Please enter 'D' to use the default directory or 'C' to enter a custom file path.")

    # Construct the full path to the selected file or directory
    file_path = selected_item

    title = input("Enter video title: ")
    description = input("Enter video description: ")

    # Use default value for location description
    default_location_description = DEFAULT_LOCATION
    location_description = input(f"Enter location description (default: {default_location_description}): ").strip()
    location_description = location_description if location_description else default_location_description

    # Ask if the user wants to schedule the video
    schedule_choice = input("Do you want to schedule the video (y/n)? ").strip().lower()
    publish_at = None
    if schedule_choice == 'y':
        # Get user inputs for date and time with defaults
        default_date = datetime.now().strftime("%Y-%m-%d")
        publish_at_date = input(f"Enter scheduled publish date (YYYY-MM-DD, default: {default_date}): ").strip()
        publish_at_date = publish_at_date if publish_at_date else default_date

        default_time = DEFAULT_UPLOAD_TIME
        publish_at_time = input(f"Enter scheduled publish time (hh:mm:ssZ, default: {default_time}): ").strip()
        publish_at_time = publish_at_time if publish_at_time else default_time

        publish_at = f"{publish_at_date}T{publish_at_time}"

    thumbnail_path = input("Enter the path of the thumbnail image (leave blank if not adding): ")

    print("Starting upload...")

    # Construct the video resource body
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': '22'  # Change as needed
        },
        'status': {
            'privacyStatus': 'private',
            'publishAt': publish_at if publish_at else None
        },
        'recordingDetails': {
            'locationDescription': location_description
        }
    }

    # Expand ~ to the user's home directory
    file_path = os.path.expanduser(file_path)

    # Create a MediaFileUpload object with a chunksize and resumable set to True
    media_file = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)

    # Create a request to insert the video
    request = youtube.videos().insert(
        part="snippet,status,recordingDetails",
        body=body,
        media_body=media_file
    )

    # Execute the request with the custom progress indicator
    response = None
    total_dots = 50
    last_progress = 0
    while response is None:
        start_time = time.time()
        status, response = request.next_chunk()
        end_time = time.time()

        if status:
            percent_complete = int(status.resumable_progress * 100 / status.total_size)
            num_dots = int(total_dots * percent_complete / 100)

            # Calculate speed
            bytes_uploaded = status.resumable_progress - last_progress
            last_progress = status.resumable_progress
            time_taken = end_time - start_time
            if time_taken > 0:
                speed = bytes_uploaded / time_taken  # bytes per second
                speed_kbps = speed / 1024  # Convert to kilobytes per second
            else:
                speed_kbps = 0

            bar = f"Uploaded {percent_complete:3d}% |{'.' * num_dots}{' ' * (total_dots - num_dots)}| {speed_kbps:,.0f} kB/s"
            print(f"\r{bar}", end='')

    print()  # Move to the next line after completion
    print("Video upload complete.")

    # Upload thumbnail if needed
    if thumbnail_path:
        print("Uploading thumbnail...")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print("Uploaded thumbnail.")

    print("Video upload process completed.")


def main():
    youtube = get_authenticated_service()

    uploads_playlist_id = get_my_uploads_list(youtube)

    print()

    list_my_uploaded_videos(youtube, uploads_playlist_id, max_results=5)

    while True:
        print("\nOptions:")
        print("1: List my uploaded videos")
        print("2: List my uploaded videos with comment counts")
        print("3: Get a video's details")
        print("4: Edit a video")
        print("5: Upload a new video")
        print("6: List unreplied comments on a video")
        print("0: Exit")
        choice = input("Enter choice: ")
        print()

        if choice == "1":
            list_my_uploaded_videos(youtube, uploads_playlist_id)
        elif choice == "2":
            list_videos_with_comment_count(youtube, uploads_playlist_id)
        elif choice == "3":
            get_video(youtube)
        elif choice == "4":
            edit_video(youtube)
        elif choice == "5":
            upload_video(youtube)
        elif choice == "6":
            list_unreplied_comments(youtube)
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please enter a valid number.")

if __name__ == "__main__":
    main()


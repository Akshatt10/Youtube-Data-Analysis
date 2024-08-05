import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
import pandas as pd

API_KEY = 'AIzaSyBkO84Nck7WgubUxS9cywUDYEQoVojVqZY'

def fetch_channel_data(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_channel_status(youtube, channel_ids):
        all_data = []
        request = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            id=','.join(channel_ids)
        )
        response = request.execute()
        for i in range(len(response['items'])):
            data = {
                'Channel_name': response['items'][i]['snippet']['title'],
                'Subscribers': response['items'][i]['statistics']['subscriberCount'],
                'Total_views': response['items'][i]['statistics']['viewCount'],
                'Total_videos': response['items'][i]['statistics']['videoCount'],
                'playlist_id': response['items'][i]['contentDetails']['relatedPlaylists']['uploads']
            }
            all_data.append(data)
        return all_data
    
    channel_data = get_channel_status(youtube, [channel_id])
    return channel_data

def fetch_video_stats(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    video_ids = []

    def get_video_ids(youtube, playlist_id):
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50
        )
        response = request.execute()

        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        more_pages = True

        while more_pages:
            if next_page_token is None:
                more_pages = False
            else:
                request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                for i in range(len(response['items'])):
                    video_ids.append(response['items'][i]['contentDetails']['videoId'])

                next_page_token = response.get('nextPageToken')

        return len(video_ids)

    get_video_ids(youtube, playlist_id)

    def extract_video_stats(youtube, video_ids):
        all_video_stats = []

        for i in range(0, len(video_ids), 50):
            request = youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids[i:i+50])
            )
            response = request.execute()

            for video in response['items']:
                video_stats = dict(
                    Title=video['snippet']['title'],
                    Published_date=video['snippet']['publishedAt'],
                    Views=video['statistics'].get('viewCount', 0),
                    Likes=video['statistics'].get('likeCount', 0),
                    Comments=video['statistics'].get('commentCount', 0),
                    Duration=video['contentDetails']['duration']
                )
                all_video_stats.append(video_stats)

        return all_video_stats

    video_data = extract_video_stats(youtube, video_ids)
    return video_data

def analyze_data(video_data):
    video_details = pd.DataFrame(video_data)
<<<<<<< HEAD
    video_details['Views'] = pd.to_numeric(video_details['Views'])
    video_details['Comments'] = pd.to_numeric(video_details['Comments'])
    
    # Convert duration to seconds
    video_details['Duration'] = pd.to_timedelta(video_details['Duration']).dt.total_seconds()

    # Separate short videos (less than 60 seconds) from regular videos
=======
    video_details['Published_date'] = pd.to_datetime(video_details['Published_date'])
    video_details['Views'] = pd.to_numeric(video_details['Views'])
    video_details['Comments'] = pd.to_numeric(video_details['Comments'])
    
    # Filter for the last 2 years
    end_date = pd.Timestamp('today')
    start_date = end_date - pd.DateOffset(years=2)
    video_details = video_details[video_details['Published_date'] >= start_date]

    # Convert duration to seconds for fetching the SHORTS in coming code
    video_details['Duration'] = pd.to_timedelta(video_details['Duration']).dt.total_seconds()

    # Separating the short videos that is the videos which are < 60 seconds
>>>>>>> ed5dd0c3991d4da118618d49b182e88888d908d2
    shorts = video_details[video_details['Duration'] < 60]
    regular_videos = video_details[video_details['Duration'] >= 60]

    # Top 10 normal videos based on views
    top10_videos = regular_videos.sort_values(by='Views', ascending=False).head(10)
    top10_shorts = shorts.sort_values(by='Views', ascending=False).head(10)

<<<<<<< HEAD
    # Extract month and year from the published date
    video_details['Month'] = pd.to_datetime(video_details['Published_date']).dt.to_period('M').astype(str)
=======
    # Month data for Shorts and regular videos
    video_details['Month'] = video_details['Published_date'].dt.strftime('%Y-%b')
>>>>>>> ed5dd0c3991d4da118618d49b182e88888d908d2

    # Group by month and year for all videos
    videos_per_month = video_details.groupby('Month').size().reset_index(name='size')

    # Sort by month and year
    videos_per_month['Month'] = pd.to_datetime(videos_per_month['Month'], format='%Y-%m')
    videos_per_month = videos_per_month.sort_values('Month')

    # Plotting videos per month
    plt.figure(figsize=(12, 8))
    sns.barplot(x='Month', y='size', data=videos_per_month, palette='viridis')
    plt.title('Number of Videos Published per Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Videos')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    # Extract month and year from the published date for shorts
    shorts['Month'] = pd.to_datetime(shorts['Published_date']).dt.to_period('M').astype(str)
    shorts_per_month = shorts.groupby('Month').size().reset_index(name='size')

    # Sort by month and year
    shorts_per_month['Month'] = pd.to_datetime(shorts_per_month['Month'], format='%Y-%m')
    shorts_per_month = shorts_per_month.sort_values('Month')

    return top10_videos, top10_shorts, videos_per_month, shorts_per_month




# STARTING BUILDING THE STREAMLIT APP....

st.title('YouTube Channel Data Analytics')

channel_name = st.text_input('Enter the YouTube Channel Name:')

if st.button('Get Channel Data'):
    if channel_name:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        # Fetching the channel ID from channel name
        def get_channel_id(youtube, channel_name):
            request = youtube.search().list(
                part='snippet',
                q=channel_name,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            if response['items']:
                return response['items'][0]['snippet']['channelId']
            else:
                return None
        
        channel_id = get_channel_id(youtube, channel_name)
        
        if channel_id:
            channel_data = fetch_channel_data(API_KEY, channel_id)
            
            # Displaying the channel information
            st.header('Channel Information')
            channel_title = channel_data[0]['Channel_name']
            subscriber_count = channel_data[0]['Subscribers']
            view_count = channel_data[0]['Total_views']
            
            st.write(f'**Channel Title:** {channel_title}')
            st.write(f'**Subscriber Count:** {subscriber_count}')
            st.write(f'**Total Views:** {view_count}')
            
            # Fetching and analyzing video information
            playlist_id = channel_data[0]['playlist_id']
            video_data = fetch_video_stats(API_KEY, playlist_id)
            top10_videos, top10_shorts, videos_per_month, shorts_per_month = analyze_data(video_data)
            
            # Displayingg top 10 videos
            st.write('Top 10 Videos by Views')
            st.write(top10_videos)
            
            # Display and plot top 10 videos by views
            plt.figure(figsize=(12, 8))
            sns.barplot(data=top10_videos, x='Views', y='Title', palette='viridis')
            plt.title('Top 10 Videos by Views')
            plt.xlabel('Views')
            plt.ylabel('Title')
            plt.tight_layout()
            st.pyplot(plt.gcf())
            
            # Display and plot videos per month
            st.write('Number of Videos Published per Month')
            plt.figure(figsize=(12, 8))
            sns.barplot(x=videos_per_month['Month'].dt.strftime('%Y-%b'), y='size', data=videos_per_month, palette='viridis')
            plt.title('Number of Videos Published per Month')
            plt.xlabel('Month')
            plt.ylabel('Number of Videos')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(plt.gcf())
            
            # Displaying and ploting shorts only if available
            if not top10_shorts.empty:
                st.write('Top 10 Shorts by Views')
                st.write(top10_shorts)
                
                plt.figure(figsize=(12, 8))
                sns.barplot(data=top10_shorts, x='Views', y='Title', palette='viridis')
                plt.title('Top 10 Shorts by Views')
                plt.xlabel('Views')
                plt.ylabel('Title')
                plt.tight_layout()
                st.pyplot(plt.gcf())
                
                st.write('Number of Shorts Published per Month')
                plt.figure(figsize=(12, 8))
                sns.barplot(x=shorts_per_month['Month'].dt.strftime('%Y-%b'), y='size', data=shorts_per_month, palette='viridis')
                plt.title('Number of Shorts Published per Month')
                plt.xlabel('Month')
                plt.ylabel('Number of Shorts')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(plt.gcf())
            else:
                st.write('This channel does not post any short videos.')
        else:
            st.error('Channel not found. Please check the channel name.')
    else:
        st.error('Please enter the Channel Name.')

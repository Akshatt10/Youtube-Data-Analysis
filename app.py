import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
import pandas as pd

API_KEY = 'AIzaSyBkO84Nck7WgubUxS9cywUDYEQoVojVqZY'

# Fetching the channel data!!
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

# Fetching Video Stats of the given channel
def fetch_video_stats(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    video_ids = []

    def get_video_ids(youtube , playlist_id):
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

    get_video_ids(youtube , playlist_id)

    def extract_video_stats(youtube , video_ids):
        all_video_stats = []

        for i in range(0 , len(video_ids) , 50):
            request = youtube.videos().list(
                part='snippet,statistics',
                id=','.join(video_ids[i:i+50])
            )
            response = request.execute()

            for video in response['items']:
                video_stats = dict(
                    Title=video['snippet']['title'],
                    Published_date=video['snippet']['publishedAt'],
                    Views=video['statistics'].get('viewCount', 0),
                    Likes=video['statistics'].get('likeCount', 0),
                    Comments=video['statistics'].get('commentCount', 0)
                )
                all_video_stats.append(video_stats)

        return all_video_stats

    video_data = extract_video_stats(youtube , video_ids)
    return video_data

def analyze_data(video_data):
    video_details = pd.DataFrame(video_data)
    video_details['Published_date'] = pd.to_datetime(video_details['Published_date']).dt.date
    video_details['Views'] = pd.to_numeric(video_details['Views'])
    video_details['Comments'] = pd.to_numeric(video_details['Comments'])

    # Top 10 videos by views
    top10 = video_details.sort_values(by='Views', ascending=False).head(10)

    # Plotting the top 10 videos
    plt.figure(figsize=(12, 8))
    ax1 = sns.barplot(data=top10, x='Views', y='Title', palette='viridis')
    ax1.set_title('Top 10 Videos by Views')
    ax1.set_xlabel('Views')
    ax1.set_ylabel('Title')
    plt.show()
    
   #Month data
    video_details['Month'] = pd.to_datetime(video_details['Published_date']).dt.strftime('%b')
    
    # Group by month
    videos_per_month = video_details.groupby('Month', as_index=False).size()
    
    # Sort by month
    sort_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    videos_per_month.index = pd.CategoricalIndex(videos_per_month.index, categories=sort_order, ordered=True)
    videos_per_month = videos_per_month.sort_index()
    
    # Plotting videos per month
    plt.figure(figsize=(12, 8))
    ax2 = sns.barplot(x='Month', y='size', data=videos_per_month, palette='viridis')
    ax2.set_title('Number of Videos Published per Month')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Number of Videos')
    plt.show()

    return top10, videos_per_month

st.title('YouTube Channel Data Analytics')

channel_id = st.text_input('Enter the YouTube Channel ID:')

if st.button('Get Channel Data'):
    if channel_id:
        channel_data = fetch_channel_data(API_KEY, channel_id)
        
        # Display channel information
        st.header('Channel Information')
        channel_title = channel_data[0]['Channel_name']
        subscriber_count = channel_data[0]['Subscribers']
        view_count = channel_data[0]['Total_views']
        
        st.write(f'**Channel Title:** {channel_title}')
        st.write(f'**Subscriber Count:** {subscriber_count}')
        st.write(f'**Total Views:** {view_count}')
        
        # Fetch and analyze video information
        playlist_id = channel_data[0]['playlist_id']
        video_data = fetch_video_stats(API_KEY, playlist_id)
        top10, videos_per_month = analyze_data(video_data)
        
        # Display top 10 videos
        st.write('Top 10 Videos by Views')
        st.write(top10)
        
        # Display and plot top 10 videos by views
        plt.figure(figsize=(12, 8))
        sns.barplot(data=top10, x='Views', y='Title', palette='viridis')
        plt.title('Top 10 Videos by Views')
        plt.xlabel('Views')
        plt.ylabel('Title')
        st.pyplot(plt.gcf())
        
        # Display and plot videos per month
        plt.figure(figsize=(12, 8))
        sns.barplot(x='Month', y='size', data=videos_per_month, palette='viridis')
        plt.title('Number of Videos Published per Month')
        plt.xlabel('Month')
        plt.ylabel('Number of Videos')
        st.pyplot(plt.gcf())
        
    else:
        st.error('Please enter the Channel ID.')

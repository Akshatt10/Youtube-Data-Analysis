import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
import pandas as pd

API_KEY = 'AIzaSyBkO84Nck7WgubUxS9cywUDYEQoVojVqZY'

def fetch_channel_data(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        id=channel_id
    )
    response = request.execute()
    data = response['items'][0]
    channel_data = {
        'Channel_name': data['snippet']['title'],
        'Subscribers': data['statistics']['subscriberCount'],
        'Total_views': data['statistics']['viewCount'],
        'Total_videos': data['statistics']['videoCount'],
        'playlist_id': data['contentDetails']['relatedPlaylists']['uploads']
    }
    return channel_data

def fetch_video_stats(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    video_ids = []
    request = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=playlist_id,
        maxResults=50
    )
    while request:
        response = request.execute()
        video_ids += [item['contentDetails']['videoId'] for item in response['items']]
        request = youtube.playlistItems().list_next(request, response)
    
    video_data = []
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()
        for video in response['items']:
            video_stats = {
                'Title': video['snippet']['title'],
                'Published_date': video['snippet']['publishedAt'],
                'Views': video['statistics'].get('viewCount', 0),
                'Likes': video['statistics'].get('likeCount', 0),
                'Comments': video['statistics'].get('commentCount', 0),
                'Duration': video['contentDetails']['duration']
            }
            video_data.append(video_stats)
    return video_data

def prepare_data(video_data):
    video_details = pd.DataFrame(video_data)
    video_details['Published_date'] = pd.to_datetime(video_details['Published_date'])
    video_details['Views'] = pd.to_numeric(video_details['Views'])
    video_details['Comments'] = pd.to_numeric(video_details['Comments'])
    video_details['Duration'] = pd.to_timedelta(video_details['Duration']).dt.total_seconds()
    
    # Aggregate data by year
    video_details['Year'] = video_details['Published_date'].dt.year
    videos_per_year = video_details.groupby('Year').size().reset_index(name='Count')
    
    # Filter out videos shorter than 60 seconds
    long_videos = video_details[video_details['Duration'] > 60]
    shorts = video_details[video_details['Duration'] <= 60]
    
    # Determine top 10 videos by views from long videos only
    top10_videos_all_time = long_videos.sort_values(by='Views', ascending=False).head(10)
    top10_shorts_all_time = shorts.sort_values(by='Views', ascending=False).head(10)
    
    return top10_videos_all_time, top10_shorts_all_time, videos_per_year, shorts

def plot_videos_per_year(videos_per_year):
    plt.figure(figsize=(12, 8))
    sns.barplot(x='Year', y='Count', data=videos_per_year, palette='viridis')
    plt.title('Number of Videos Published per Year')
    plt.xlabel('Year')
    plt.ylabel('Number of Videos')
    plt.tight_layout()
    return plt.gcf()

def plot_shorts_per_month(shorts):
    shorts_per_month = shorts.groupby(shorts['Published_date'].dt.to_period('M').astype(str)).size().reset_index(name='Count')
    shorts_per_month = shorts_per_month.sort_values('Published_date')
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x='Published_date', y='Count', data=shorts_per_month, palette='viridis')
    plt.title('Number of Shorts Published per Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Shorts')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return plt.gcf()

def plot_top10_shorts(top10_shorts):
    plt.figure(figsize=(12, 8))
    sns.barplot(data=top10_shorts, x='Views', y='Title', palette='viridis')
    plt.title('Top 10 Shorts by Views (All Time)')
    plt.xlabel('Views')
    plt.ylabel('Title')
    plt.tight_layout()
    return plt.gcf()

# BUILDING STREAMLIT APP.....

st.title('YouTube Channel Data Analytics')

channel_name = st.text_input('Enter the YouTube Channel Name:')

if st.button('Get Channel Data'):
    if channel_name:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.search().list(
            part='snippet',
            q=channel_name,
            type='channel',
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            channel_id = response['items'][0]['snippet']['channelId']
            channel_data = fetch_channel_data(API_KEY, channel_id)
            st.header('Channel Information')
            st.write(f"**Channel Title:** {channel_data['Channel_name']}")
            st.write(f"**Subscriber Count:** {channel_data['Subscribers']}")
            st.write(f"**Total Views:** {channel_data['Total_views']}")
            
            video_data = fetch_video_stats(API_KEY, channel_data['playlist_id'])
            
            top10_videos_all_time, top10_shorts_all_time, videos_per_year, shorts = prepare_data(video_data)
            
            st.write('Top 10 Videos by Views (All Time)')
            st.write(top10_videos_all_time[['Title', 'Views', 'Published_date']])
            
            st.write('Number of Videos Published per Year')
            st.pyplot(plot_videos_per_year(videos_per_year))
            
            if not shorts.empty:
                st.write('Top 10 Shorts by Views (All Time)')
                st.write(top10_shorts_all_time[['Title', 'Views', 'Published_date']])
                st.pyplot(plot_top10_shorts(top10_shorts_all_time))
                
                st.write('Number of Shorts Published per Month')
                st.pyplot(plot_shorts_per_month(shorts))
            else:
                st.write('This channel does not post any short videos.')
        else:
            st.error('Channel not found. Please check the channel name.')
    else:
        st.error('Please enter the Channel Name.')

from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from dateutil import parser
from config import api_key

class Service():
    def __init__(self):
        self.service = None
    
    def create_service(self, api_name: str, api_version: str, api_key: str):
        '''
            Takes in API_Name, version of the API, and API_Key to create a connection to the API.
            The connection is persistent, and needs to be closed if not in use.
        '''
        self.service = build(api_name, api_version, developerKey=api_key)
        
    def make_request(self, resource_type, method, part: str, **kwargs):
        '''
            Takes in resource_type which are data entity with unique identifiers, such as channels, and videos which are used to interact using the API.
            https://developers.google.com/youtube/v3/getting-started#resources has list of resource types.
            Takes in method, which are supported by the API, for youtube it takes in list, insert, update, and delete to make requests.
            Part is a required parameter for API request that retrieves or returns a resource. https://developers.google.com/youtube/v3/getting-started#part
            **kwargs for any other parameters needed to make a request to the API
        '''

        resource = getattr(youtube_build, resource_type)()
        method = getattr(resource, method)

        request = method(
            part = part,
            **kwargs
        )

        response = request.execute()
        
        return response
    
    def close_service(self, service):
        '''
            Closes the service
        '''
        service.close()

#create a service, making a persistent connection with the youtube API

youtube_service = Service()
youtube_service.create_service(
    api_name = "youtube",
    api_version = "v3",
    api_key=api_key
)

youtube_build = youtube_service.service

#make request about a specific channel in order to obtain the uploads playlist id
channel_info = youtube_service.make_request(
    resource_type = "channels",
    part = 'contentDetails',
    method = "list",
    forUsername = "GoogleDevelopers"
    )

uploadsId = channel_info['items'][0]["contentDetails"]["relatedPlaylists"]["uploads"]

# #Obtain information about all the uploaded videos on the channel, upto maximum results of 50, using the upload id obtain previously
channel_upload_info = youtube_service.make_request(
    resource_type = "playlistItems",
    method = "list",
    part = 'snippet',
    playlistId = uploadsId,
    maxResults = 50
)


publishedAt_info = dict()

#filtered all the uploaded videos on the channel based on the published date up to 6 months. There are multiple pages to a channel, in the future incorporate multiple pages from channel_upload_info. Stored them  in a dict
date = datetime.now()
for item in channel_upload_info["items"]:
    for info in item:
        if info == "snippet":
            if parser.parse(item["snippet"]["publishedAt"]).replace(tzinfo=None) >= date - relativedelta(months=+6):
                publishedAt_info.update({item["snippet"]["publishedAt"]: item["snippet"]["resourceId"]["videoId"]})

#made a reqeust for individual videos present on the channel, upto 6 months, or how many are in the page and stored the view count of each video in the dict along with the video id.
for k,v in publishedAt_info.items():
    video_info = youtube_service.make_request(
        resource_type = "videos",
        method = "list",
        part = 'statistics',
        id = v
    )
    for item in video_info["items"]:
        for info in item:
            if info == "statistics":
                viewCount = item["statistics"]["viewCount"]
                publishedAt_info[k] = [v, viewCount]
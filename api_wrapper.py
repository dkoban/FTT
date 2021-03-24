import requests
import os
import json
import pandas as pd
import math

def get_users(usernames): 
    """Query a user screen name for profile information.

    Args:
        usernames: list of user screen names to query
    Returns:
        Dataframe of profile information (user_id, username, name, description, location, created_at, followers_count, following_count, tweet_count, listed_count).    

    """
    # authenticate with end point
    bearer_token = os.environ.get("BEARER_TOKEN")    
    
    # generate query string
    if type(usernames) != list:
        usernames_qterm = 'usernames=' + usernames
    else:
        usernames_qterm = 'usernames=' + ','.join(usernames)    
    user_fields = "user.fields=description,created_at,entities,id,location,name,public_metrics,url,username,verified"
    url = "https://api.twitter.com/2/users/by?{}&{}".format(usernames_qterm, user_fields)
    
    # submit GET request - submit a query to the API      
    response = requests.request("GET", url, 
                                headers = {"Authorization": "Bearer {}".format(bearer_token)})   
    
    # parse the json response into a dataframe
    users = pd.DataFrame(response.json()['data'])
    users['followers_count'] = users['public_metrics'].apply(lambda x: x['followers_count'])
    users['following_count'] = users['public_metrics'].apply(lambda x: x['following_count'])
    users['tweet_count'] = users['public_metrics'].apply(lambda x: x['tweet_count'])
    users['listed_count'] = users['public_metrics'].apply(lambda x: x['listed_count'])
    users = users.rename(columns = {'id':'user_id'})
    
    # error handling to prevent failing when columns are missing in the json response
    empty_df = pd.DataFrame({'user_id': [], 'username': [],'name': [],'description': [], 
                             'location': [],'created_at': [],'followers_count': [],'following_count': [],
                             'tweet_count': [],'listed_count': []})
    users = pd.concat([empty_df, users])
    
    users = users[['user_id','username','name','description','location','created_at','followers_count','following_count','tweet_count','listed_count']]    
    return users 

def lookup_followed_accounts_simple(username, token = 0): 
    """Query a user screen name for information about 100 accounts they follow.

    Args:
        usernames: user screen name to query
    Returns:
        Dataframe of profile information (user_id, username, name, description, location, created_at, followers_count, following_count, tweet_count, listed_count).    

    """ 
    # authenticate with end point
    bearer_token = os.environ.get("BEARER_TOKEN")  
    
    # query profile info to get a user_id
    user_info = get_users(username)
    user_id = user_info['user_id'][0]
        
    # generate query string
    # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
    if token == 0: 
        url =  'https://api.twitter.com/2/users/' + user_id + '/following?user.fields=description,created_at,entities,id,location,name,public_metrics,url,username,verified&max_results=100'
    else:
        url =  'https://api.twitter.com/2/users/' + user_id + '/following?user.fields=description,created_at,entities,id,location,name,public_metrics,url,username,verified&max_results=100&pagination_token=' + token    

    # submit GET request - submit a query to the API      
    response = requests.request("GET", url,
                                headers = {"Authorization": "Bearer {}".format(bearer_token)})

    return response.json()


def lookup_followed_accounts(username, record_count = 10): 
    # authenticate with end point
    bearer_token = os.environ.get("BEARER_TOKEN")
    
    user_info = get_users(username)
    user_id = user_info['user_id'][0]
    
    # generate query string
    if record_count <= 100:
        first_request = lookup_followed_accounts_simple(username, token = 0)           
    else:
        first_request = lookup_followed_accounts_simple(username, token = 0)        
        status = "keep_going"
    
    try: 
        next_token = first_request['meta']['next_token']              
        followed_dfs = []
        batch_count = math.ceil(record_count/100)
        n = 1  
        
        while (status != "done") & (n <= batch_count):
            status = update_status(last_request = first_request)
            
            while (status != "done") & (n <= batch_count):
                resp = lookup_followed_accounts_simple(username, token = next_token)
                print("token: " + next_token) 
                followed_dfs.append(resp)
                status = update_status(last_request = resp)                  
                n += 1
                try: 
                    next_token = resp['meta']['next_token']
                except:
                    token = "done"
                    status = 'done'         
            
        # combine results into a single dataframe
        followed_accounts = []           
        for i in range(0, len(followed_dfs)):
            followed_accounts.append(pd.DataFrame(followed_dfs[i]['data']))
        followed_accounts = pd.concat(followed_accounts)        
    
    except:
        followed_accounts = pd.DataFrame(first_request['data'])       
        
    # parse the json response into a dataframe    
    followed_accounts['followers_count'] = followed_accounts['public_metrics'].apply(lambda x: x['followers_count'])
    followed_accounts['following_count'] = followed_accounts['public_metrics'].apply(lambda x: x['following_count'])
    followed_accounts['tweet_count'] = followed_accounts['public_metrics'].apply(lambda x: x['tweet_count'])
    followed_accounts['listed_count'] = followed_accounts['public_metrics'].apply(lambda x: x['listed_count'])
    followed_accounts = followed_accounts.rename(columns = {'id':'user_id'})

    # error handling to prevent failing when columns are missing in the json response
    empty_df = pd.DataFrame({'user_id': [], 'username': [],'name': [],'description': [], 
                             'location': [],'created_at': [],'followers_count': [],'following_count': [],
                             'tweet_count': [],'listed_count': []})
    followed_accounts = pd.concat([empty_df, followed_accounts])

    followed_accounts = followed_accounts[['user_id','username','name','description','location','created_at','followers_count','following_count','tweet_count','listed_count']]    
    return followed_accounts  

def get_user_activity_simple(username, token = 0):
    # authenticate with end point
    bearer_token = os.environ.get("BEARER_TOKEN")
    
    # query profile info to get a user_id
    user_info = get_users(username)
    user_id = user_info['user_id'][0]
    
    # generate query string
    # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
    if token == 0: 
        url =  'https://api.twitter.com/2/users/' + user_id + '/tweets?tweet.fields=conversation_id,in_reply_to_user_id,created_at,author_id,entities,public_metrics,geo,lang,referenced_tweets&max_results=5'
    else:
        url =  'https://api.twitter.com/2/users/' + user_id + '/tweets?tweet.fields=conversation_id,in_reply_to_user_id,created_at,author_id,entities,public_metrics,geo,lang,referenced_tweets&max_results=100&pagination_token=' + token    
    
    # submit GET request - submit a query to the API      
    response = requests.request("GET", url, 
                                headers = {"Authorization": "Bearer {}".format(bearer_token)})   
    
    return response.json()

def check_token(response):
    try:
        next_token = response['meta']['next_token']
    except:
        next_token = "complete"
                
def update_status(last_request):
    if check_token(response = last_request) == "complete":
        status = "done"
    else:
        status = "keep_going"   
    return status

def get_user_activity0(username, record_count = 10): 
    # authenticate with end point
    bearer_token = os.environ.get("BEARER_TOKEN")
    
    user_info = get_users(username)
    user_id = user_info['user_id'][0]
    
    # generate query string
    if record_count <= 100:
        first_request = get_user_activity_simple(username, token = 0)     
    else:
        first_request = get_user_activity_simple(username, token = 0)        
        status = "keep_going"
    
    try: 
        next_token = first_request['meta']['next_token']              
        tweet_dfs = []
        batch_count = math.ceil(record_count/100)
        n = 1  
        
        while (status != "done") & (n <= batch_count):
            status = update_status(last_request = first_request)
            
            while (status != "done") & (n <= batch_count):
                resp = get_user_activity_simple(username, token = next_token)
                print("token: " + next_token) 
                tweet_dfs.append(resp)
                status = update_status(last_request = resp)                  
                n += 1
                try: 
                    next_token = resp['meta']['next_token']
                except:
                    token = "done"
                    status = 'done'         
            
        # combine results into a single dataframe
        activity = []           
        for i in range(0, len(tweet_dfs)):
            activity.append(pd.DataFrame(tweet_dfs[i]['data']))
        activity = pd.concat(activity)       
    
    except:
        activity = pd.DataFrame(first_request['data']) 
        
    activity['author_screen_name'] = username
    activity['retweet_count'] = activity['public_metrics'].apply(lambda x: x['retweet_count'])
    activity['reply_count'] = activity['public_metrics'].apply(lambda x: x['reply_count'])
    activity['like_count'] = activity['public_metrics'].apply(lambda x: x['like_count'])
    activity['quote_count'] = activity['public_metrics'].apply(lambda x: x['quote_count'])
    
    def extract_ref_tweet_type(x):     
        try:
            val = x[0]['type']
        except:
            val = 'original_tweet'
        return val

    def extract_ref_tweet_id(x):     
        try:
            val = x[0]['id']
        except:
            val = None
        return val

    activity['referenced_tweet_type'] = activity['referenced_tweets'].apply(lambda x: extract_ref_tweet_type(x))
    activity['referenced_tweet_id'] = activity['referenced_tweets'].apply(lambda x: extract_ref_tweet_id(x))
    
    return activity

def get_user_activity(usernames, record_count = 10): 
    activity = [pd.DataFrame()]
    for username in usernames:
        activity.append(get_user_activity0(username, record_count = record_count))
    activity = pd.concat(activity)
    activity.reset_index(inplace = True, drop = True)
    return activity

def extract_el(data):
    hashtag_el = [pd.DataFrame({'author_id_from':[], 'author_screen_name_from': [], 'status_id': [], 'to': []})]
    for k in range(0, len(data)):       
        try: 
            hashtags = pd.json_normalize(data['entities'][k]['hashtags'])['tag'].tolist()
            el = pd.DataFrame({'to': hashtags})            
            el['author_id_from'] = data['author_id'][k]
            el['author_screen_name_from'] = data['author_screen_name'][k]
            el['status_id'] = data['id'][k]
            el = el[['author_id_from', 'author_screen_name_from', 'status_id', 'to']]
            hashtag_el.append(el)
        except:
            pass
        
    hashtag_el = pd.concat(hashtag_el)
    hashtag_el.reset_index(drop = True, inplace = True)
    hashtag_el['edge_type'] = 'hashtag'
        
    mention_el = [pd.DataFrame({'author_id_from':[], 'author_screen_name_from': [], 'status_id': [], 'to': []})]
    for k in range(0, len(data)):       
        try: 
            mentioned_user = pd.json_normalize(data['entities'][k]['mentions'])['username'].tolist()
            el = pd.DataFrame({'to': mentioned_user})
            el['author_id_from'] = data['author_id'][k]
            el['author_screen_name_from'] = data['author_screen_name'][k]
            el['status_id'] = data['id'][k]
            el = el[['author_id_from', 'author_screen_name_from', 'status_id', 'to']]            
            mention_el.append(el)
        except:
            pass
            
    mention_el = pd.concat(mention_el)
    mention_el.reset_index(drop = True, inplace = True)
    mention_el['edge_type'] = 'mention'

    url_el = [pd.DataFrame({'author_id_from':[], 'author_screen_name_from': [], 'status_id': [], 'to': []})]
    for k in range(0, len(data)):       
        try: 
            mentioned_user = pd.json_normalize(data['entities'][k]['urls'])['url'].tolist()
            el = pd.DataFrame({'to': mentioned_user})
            el['author_id_from'] = data['author_id'][k]
            el['author_screen_name_from'] = data['author_screen_name'][k]
            el['status_id'] = data['id'][k]
            el = el[['author_id_from', 'author_screen_name_from', 'status_id', 'to']]            
            url_el.append(el)
        except:
            pass
            
    url_el = pd.concat(url_el)
    url_el.reset_index(drop = True, inplace = True)
    url_el['edge_type'] = 'url'
    
    el = pd.concat([hashtag_el, mention_el, url_el])
    el.reset_index(drop = True, inplace = True)

    return el
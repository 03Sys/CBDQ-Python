import os, json, tweepy, time, random, requests, re, sys
import keep_alive  # at the top


keep_alive.keep_alive()

consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
bearer_token = ""

cur_version = "1.0.6"

# Use twitter api V2
Client = tweepy.Client(bearer_token=bearer_token, 
                       consumer_key=consumer_key, 
                       consumer_secret=consumer_secret, 
                       access_token=access_token, 
                       access_token_secret=access_token_secret
)
auth = tweepy.OAuth1UserHandler(consumer_key,
                                consumer_secret,
                                access_token,
                                access_token_secret
)
# for media upload
api = tweepy.API(auth, wait_on_rate_limit=True)

# Verify Credentials
try:
    api.verify_credentials()
    print("Authenticated.")
except:
    print("Error during authentication.")
    sys.exit()

# The time between every new tweet
# This is in seconds, so 3600 is 1 hour
time_between_tweets = 3600

# read bot.json
botjson = open("bot.json", "r", encoding="utf-8")
botjson = json.load(botjson)

global blahList
global mediaIDs
global imgList
global otherList
global videoList
blahList = []
mediaIDs = []
imgList = []
otherList = []
videoList = []

def resetLists():
    blahList.clear()
    mediaIDs.clear()
    imgList.clear()
    otherList.clear()
    videoList.clear()

def generateTweet():
    tweet = random.choice(botjson["origin"])
    resetLists()

    # get all the #blah# in the tweet,can also be given as a lowercase, uppercase, numbers, special characters, spaces, etc
    for blah in re.findall(r"#[a-zA-Z0-9]+#", tweet):
        blahList.append(blah)

    # replace the #blah# with a random word from the blah array
    for blah in blahList:
        choice = random.choice(botjson[blah[1:-1]])
        
        while choice in otherList:
            choice = random.choice(botjson[blah[1:-1]])
        otherList.append(choice)

        tweet = tweet.replace(blah, choice, 1)
        # check if theres another #blah# in the tweet, can be character, item, etc
        if re.findall(r"#[a-zA-Z0-9]+#", tweet):
            for blah in re.findall(r"#[a-zA-Z0-9]+#", tweet):
                choice = random.choice(botjson[blah[1:-1]])
                
                while choice in otherList:
                    choice = random.choice(botjson[blah[1:-1]])
                otherList.append(choice)

                tweet = tweet.replace(blah, choice, 1)
        #print(f"Replaced {blah} with {choice}")

    # get all the {img link} in the tweet
    for img in re.findall(r"{img \S+}", tweet):
        imgList.append(img)
        # remove it from the tweet
        tweet = tweet.replace(img, "")

    # get all the {vid link} in the tweet
    for vid in re.findall(r"{vid \S+}", tweet):
        videoList.append(vid)
        # remove it from the tweet
        tweet = tweet.replace(vid, "")

    for img in imgList:
        # download the image w/ requests
        image = img.split("{img ")[1]
        image = image.split("}")[0]
        image_name = image.split("/")[-1]
        # sometimes the image link can have a query string, so we need to remove it
        if "?" in image_name:
            image_name = image_name.split("?")[0]

        r = requests.get(image, allow_redirects=True)
        try:
            try:
                open(image_name, "wb").write(r.content)
            except:
                image_name = "temp.png"
                open("temp.png", "wb").write(r.content)
        except:
            image_name = "unknown.png"

        # upload the image to twitter
        try:
            media = api.media_upload(image_name)
        except:
            image_name = "unknown.png"
            media = api.media_upload(image_name)
        print(f"Uploaded image: {image_name}")
        mediaIDs.append(media.media_id)

        # replace the {img link} with nothing
        tweet = tweet.replace(img, "")

    for vid in videoList:
        # download the video w/ requests
        video = vid.split("{vid ")[1]
        video = video.split("}")[0]
        video_name = video.split("/")[-1]
        # sometimes the video link can have a query string, so we need to remove it
        if "?" in video_name:
            video_name = video_name.split("?")[0]
        r = requests.get(video, allow_redirects=True)
        try:
            try:
                open(video_name, "wb").write(r.content)
            except:
                video_name = "temp.mp4"
                open("temp.mp4", "wb").write(r.content)
        except:
            video_name = "unknown.mp4"

        # upload the video to twitter
        media = api.media_upload(video_name)
        print(f"Uploaded video: {video_name}")
        mediaIDs.append(media.media_id)

        # replace the {vid link} with nothing
        tweet = tweet.replace(vid, "")

    return tweet
now = 0
while True:
    timer = time.time()
    
    #print(f"Time since last tweet: {timer - (now or 0)}")
    if timer - (now or 0) >= time_between_tweets:
        try:
            print("Tweeting...")
        except:
            pass

        # get a random tweet from the origin array
        tweet = generateTweet()

        # tweet the tweet
        try:
            try:
                if len(mediaIDs) == 0:
                    Client.create_tweet(text=tweet)
                else:
                    Client.create_tweet(text=tweet, media_ids=mediaIDs)
            except:
                # keep generating tweets until it works
                while True:
                    tweet = generateTweet()
                    try:
                        Client.create_tweet(text=tweet, media_ids=mediaIDs)
                        break
                    except:
                        # if error is <tweepy.errors.BadRequest>
                        # print possible error
                        print("Error: ", sys.exc_info()[0])
                        if sys.exc_info()[0] == tweepy.errors.BadRequest:
                            print("""
Possible error!
    1. Tweet is too long.
    2. Tweet is a duplicate.
    3. API key is invalid.
                            """)
                            pass
                        elif sys.exc_info()[0] == tweepy.errors.Forbidden:
                            print("""
Possible error!
    1. API key doesn't have permission to tweet | check if it's read-only.
                            """)
                            sys.exit()
            print(f"Tweeted: {tweet}")
        except:
            print(f"Tweet failed: {tweet}")
            # print the error
            print(sys.exc_info()[0])

        # delete the images
        for image in imgList:
            image = image.split("{img ")[1]
            image = image.split("}")[0]
            image_name = image.split("/")[-1]
            # sometimes the image link can have a query string, so we need to remove it
            if "?" in image_name:
                image_name = image_name.split("?")[0]
            try:
                os.remove(image_name)
            except:
                try:
                    os.remove("temp.png")
                except:
                    print("Couldn't delete image; it probably doesn't exist.")

        # delete the videos
        for video in videoList:
            video = video.split("{vid ")[1]
            video = video.split("}")[0]
            video_name = video.split("/")[-1]
            # sometimes the video link can have a query string, so we need to remove it
            if "?" in video_name:
                video_name = video_name.split("?")[0]
            try:
                os.remove(video_name)
            except:
                try:
                    os.remove("temp.mp4")
                except:
                    print("Couldn't delete video; it probably doesn't exist.")
        now = time.time()
    else:
        time.sleep(1)

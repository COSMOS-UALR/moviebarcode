#!/usr/bin/env python3

"""
usage:
    $(virtual_env) python app.py -> This runs the default test for a single video

    # Two youtube links are added one for a single video, the other one is a playlist. If you switch to playlist
    $(virtual_env) python app.py -> This runs the default playlist version of the script
                                |_> You can change the playlist url by adding the url parameter to command line

    $(virtual_env) python app.py --yturl "youtube playlist link"
                   |_> This may take time based on the video length or number of videos as well as internet speed

"""


import cv2                                                                                     # opencv version is 4.0.0
import numpy as np
import os, sys, time
import subprocess
import argparse
import datetime
import pafy
import yaml
import json
import pprint
import httplib2
from imutils.video import FileVideoStream, FPS

# TODO: Accelerate video streaming?
# TODO: Make loggins with python logger
# TODO: Make path assigns with Python pathlib

# if you're lazy, you can use this url to test the code works for you.
default_single = 'https://www.youtube.com/watch?v=g8vHhgh6oM0'
default_playlist = 'https://www.youtube.com/playlist?list=PLhjLO-ekrsRvxL-aGqP82qgAgJlzKPDw7'


# config.yaml parse and assign to pafy api
def yaml_parser(yaml_file):
    with open('config.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data["key"]


# check if youtube link is a video list
def identify_url(url):
    status = "empty"
    if url is None:
        raise ValueError("url is empty!")
    elif "playlist" in url:
        if args["verbose"]:
            print("url is a playlist")
        status = "playlist"
    elif "watch" in url:
        if args["verbose"]:
            print("url is a single video")
        status = "single"

    return status


# validate url to make sure the link is alive
def validate_url(url):
    c = httplib2.Http()
    resp = c.request(url, "HEAD")
    return int(resp[0]["status"])


# count number of frames that this video have
def frame_count(YTURL):
    """
    :param
        YTURL: youtube video url -> it should be a single video.
    :return:
        number of frames in the video

    :usage
        n_frames = frame_count(YTURL)
    """

    video = cv2.VideoCapture(YTURL)

    # if you have opencv 3 then call quick solution
    if int(cv2.__version__.split(".")[0]) >= 3:
        if args["verbose"]:
            print("[{} | INFO] Lucky! You have opencv 3.x or 4.x version.".format(datetime.datetime.now().time()))
        num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    else:
        if args["verbose"]:
            print("[{} | INFO] It seems you don't have opencv 3.x version.".format(datetime.datetime.now().time()))

        num_frames = 0

        ret = True
        while ret:
            # read frame-by-frame where the show begins!
            ret, frame = video.read()
            num_frames += 1

    return num_frames


# if you just want to get video url no metadata
def url_only(YTURL):
    assert YTURL, str

#     result = subprocess.run(["youtube-dl", "-v", "-f", "bestvideo", YTURL, "--skip-download", "-g"], stdout=subprocess.PIPE) 
    result = subprocess.run(["youtube-dl", "-v", YTURL, "--skip-download", "-g"], stdout=subprocess.PIPE)
#     result = subprocess.run(["youtube-dl", "-v", "-f", "worstvideo[ext=mp4]", YTURL, "-g", "--skip-download"], stdout=subprocess.PIPE)
#     result = subprocess.run(["youtube-dl", YTURL, "-g","--skip-download"], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8').split()[0]
    print(f"output: {output}")
    return output


# if you just want to get video url no metadata
def video_download(YTURL):
    assert YTURL, str
    subprocess.run(["youtube-dl", YTURL])


# get the best available youtube video url from pafy object
def get_url(YTURL):
    """
    :param
        YTURL: youtube video url -> it should be a single video.
    :return:
        best available download link of the video

    :usage
        best_specs.url = get_url(YTURL)
    """

    video_pafy = pafy.new(YTURL)
    # best_specs = video_pafy.getbest(preftype="webm")  # TODO: Make dynamic this step. get the most basic ones.
    # best_specs = video_pafy.getbest()  # TODO: Make dynamic this step. get the most basic ones.

    # if args["verbose"]:                                          # if you'd like to see the video url before download.
    #     print("[{} | INFO] YTURL: {}.".format(datetime.datetime.now().time(), best_specs.url))

    # print other information about video
    pp = pprint.PrettyPrinter(indent=2)

    print("-"*(len(video_pafy.title) + 18))
    print("| Video Title:    {}".format(video_pafy.title))
    print("| Video duration: {}".format(video_pafy.duration))
    print("| Video rating:   {}".format(video_pafy.rating))
    print("| Video author:   {}".format(video_pafy.author))
    print("| Video length:   {}".format(video_pafy.length))
    print("| Video url   :   {}".format(video_pafy.getbest().url))

    # print("| Video keywords: {}".format(video_pafy.keywords))            # if you would like to see keywords in a line

    # If you would like to visualize the object as dictionary
    # pprint.pprint(video_pafy, depth=1)

    print("| Video keywords:")
    pp.pprint(video_pafy.keywords)
    print("| Video thumb:    {}".format(video_pafy.thumb))
    print("| Video videoid:  {}".format(video_pafy.videoid))
    print("| Video viewcount:{}".format(video_pafy.viewcount))
    print("-"*(len(video_pafy.title) + 18))

    return video_pafy.videoid, video_pafy.getbest().url


# generate json and png files.
def generate_barcode(video_url):
    """
    :param
        video: video object.
    :return:
        average R, G, B values of each frame in a video

    :usage
        avgs = generate_barcode(video)
    """

    assert video_url, str

    if video_url is None:
        raise ValueError("[{} | ERROR] video url is None object!".format(datetime.datetime.now().time()))

    # mean value for each frame of the video
    avgs = []

    # start the file video stream thread and allow the buffer to
    # start to fill
    print("[INFO] starting video file thread...")
    fvs = FileVideoStream(video_url).start() # TODO: Fix here, we need a url not VideoCapture object.
    time.sleep(1.0)
    # start the FPS timer
    fps = FPS().start()

    while fvs.more():
        # grab the frame from the threaded video file stream, resize
        # it, and convert it to grayscale (while still retaining 3
        # channels)
        frame = fvs.read()

        if args["display"]:
            cv2.imshow("video", frame)

        frame_avg = cv2.mean(frame)[:3]
        avgs.append(frame_avg)
        fps.update()

    if args["verbose"]:
        print("[{} | INFO] video barcode is ready. Size:{}".format(datetime.datetime.now().time(), len(avgs)))

    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    # do a bit of cleanup
    cv2.destroyAllWindows()
    fvs.stop()

    return avgs


# visualize the barcode on your screen
def vis_barcode(png_file_name=None):
    """
    :param
        None
    :return:
        None

    :usage
        Would you like to see the movie barcode on action?
    """

    # load the averages file and convert it to a NumPy array
    avgs = json.loads(open(args["json"]).read())
    np_avgs = np.array(avgs, dtype="int")

    # grab the individual bar width and allocate memory for
    # the barcode visualization
    bw = 1
    barcode = np.zeros((250, len(np_avgs) * bw, 3), dtype="uint8")

    # loop over the averages and create a single 'bar' for
    # each frame average in the list
    for (i, avg) in enumerate(np_avgs):
        # cv2.rectangle(barcode, (int(i * bw), 0), (int((i + 1) * bw), 250), tuple(avg), 3)
        cv2.rectangle(barcode, (int(i * bw), 0), (int((i + 1) * bw), 250), (int(avg[0]), int(avg[1]), int(avg[2])), 3)

    # write the video barcode visualization to file and then
    # display it to our screen
    if args["barcode"] is not None:
        cv2.imwrite(args["barcode"], barcode)

    if png_file_name is not None:
        cv2.imwrite(png_file_name, barcode)

    if args["display"]:
        cv2.imshow("Barcode", barcode)  # TODO: Add another option to visualize the image such as PIL, or scikit-image
        cv2.waitKey(0)
        if sys.platform == "linux":
            cv2.destroyAllWindows()


# scan and parse playlist into a list of single youtube video links
def parse_playlist(playlist):
    # we believe the playlist is alive and it's a playlist url

    video_ids = []
    # get the request return for pafy object for playlist
    playlist_return = pafy.get_playlist(playlist)

    if args["verbose"]:
        print("Number of videos in this play list: {}".format(len(playlist_return["items"])))

    for video in playlist_return["items"]:
        video_ids.append(video['pafy'].videoid)
        if args["verbose"]:
            print("{} | {}".format(video['pafy'].videoid, video['pafy'].title))

    return video_ids


# command-line arguments -> for more info check the usage section (top of the file)
ap = argparse.ArgumentParser()
ap.add_argument("-u", "--yturl", help="YouTube video url to download metada and movie barcode")
ap.add_argument("-v", "--video", default=True, help="Video path on your box")
ap.add_argument("-l", "--verbose", default=1, help="display debug lines")
ap.add_argument("-j", "--json", help="json file to write barcode data")
ap.add_argument("-b", "--barcode", help="path to png file to write barcode image")
ap.add_argument("-d", "--display", default=0, help="play video if you want to see")
args = vars(ap.parse_args())


# Main function, like we have in many C based languages
def main():
    key = yaml_parser("config.yaml")
    pafy.set_api_key(key=key)

    # if user hasn't entered a youtube url, no worries, we have alive one.
    if args["yturl"] is None:
        args["yturl"] = default_single
        # args["yturl"] = default_playlist

    home = os.getcwd()
    # print(cv2.getBuildInformation())                                                # Display OpenCV build information

    # Make sure video url is alive
    if validate_url(args["yturl"]) == 200:
        if args["verbose"]:
            print("[{} | INFO] YouTube url is valid!.".format(datetime.datetime.now().time()))
    else:
        raise ValueError("[{} | ERROR] YouTube url is not valid!.".format(datetime.datetime.now().time()))

    # TODO: Call identify function to check if the video is playlist or a single video
    status = identify_url(args['yturl'])
    if status == "single":
        # Do the steps for a single video
        # Verify experiment environment

        output_directory = home + "/output" + "/" + args["yturl"].split("=")[-1]
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)
        if args["json"] is None:
            json_file = output_directory + "/" + args["yturl"].split("=")[-1] + ".json"
            args["json"] = json_file

        if args["barcode"] is None:
            png_file = output_directory + "/" + args["yturl"].split("=")[-1] + ".png"
            args["barcode"] = png_file

        # Download video and generate moviebarcode later
        video_download(YTURL=args["yturl"])
        
        # Normal way of getting the url
        video_id, video_url = get_url(YTURL=args["yturl"])

#         alternative approach
#         video_url = url_only(YTURL=args["yturl"])

        # Find video file in the running directory and load with opencv
        for file_ in os.listdir("./"):
#             print(f"files: {file_}")
            if str(video_id) in file_:
                video_loc = file_
#                 print(f"video_loc={video_loc}")
                
        # print(video_url)
        num_frames = frame_count(video_loc)
            

#         # print(video_url)
#         num_frames = frame_count(video_url)

        # video = cv2.VideoCapture(video_url)

        if args["verbose"]:
            print("[{} | INFO] Number of frames: {}".format(datetime.datetime.now().time(), num_frames))

        # Write barcode data to json file
        # Check if the file is already available, delete it.
        if not os.path.exists(args["json"]):
            with open(args["json"], "w") as json_file:
                json_file.write(json.dumps(generate_barcode(video_url=video_loc)))
        else:
            os.remove(args["json"])
            with open(args["json"], "w") as json_file:
                json_file.write(json.dumps(generate_barcode(video_url=video_loc)))

        # video.release()

        if args["verbose"]:
            print("[{} | INFO] json file is being written to {}".format(datetime.datetime.now().time(), args["json"]))

        vis_barcode()
        
        os.remove(video_loc)
        if args["verbose"]:
            print("[{} | INFO] {} video file is removed".format(datetime.datetime.now().time(), video_loc))
         

    elif status == "playlist":
        video_ids = parse_playlist(args["yturl"])
        # Do the steps for a playlist

        # Verify experiment environment
        for video_idx in video_ids:
            output_directory = home + "/output" + "/" + str(video_idx)
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)
                if args["verbose"]:
                    print("[{} | INFO] Output directory is created: {}".format(datetime.datetime.now().time(),
                                                                               output_directory))
            if args["json"] is None:
                json_file = output_directory + "/" + str(video_idx) + ".json"
                args["json"] = json_file
                if args["verbose"]:
                    print("[{} | INFO] JSON file is assigned to : {}".format(datetime.datetime.now().time(), json_file))

            if args["barcode"] is None:
                png_file = output_directory + "/" + str(video_idx) + ".png"
                args["barcode"] = png_file
                if args["verbose"]:
                    print("[{} | INFO] Barcode file is assigned to : {}".format(datetime.datetime.now().time(),
                                                                                png_file))

            video_url = 'https://www.youtube.com/watch?v=' + str(video_idx)
            if args["verbose"]:
                print("[{} | INFO] Video url : {}".format(datetime.datetime.now().time(), video_url))

            # TODO: make a function after this line
            video_link = get_url(video_url)
            num_frames = frame_count(video_link)

            # video = cv2.VideoCapture(video_link)

            if args["verbose"]:
                print("[{} | INFO] Number of frames: {}".format(datetime.datetime.now().time(), num_frames))

            # Write barcode data to json file
            # Check if the file is already available, delete it.
            if not os.path.exists(args["json"]):
                with open(args["json"], "w") as json_file:
                    json_file.write(json.dumps(generate_barcode(video_url=video_link)))
            elif os.path.exists(args["json"]):
                os.remove(args["json"])
                with open(args["json"], "w") as json_file:
                    json_file.write(json.dumps(generate_barcode(video_url=video_link)))

            # video.release()

            if args["verbose"]:
                print("[{} | INFO] json file is being written to {}".format(datetime.datetime.now().time(), args["json"]))

            vis_barcode(png_file_name=png_file)
            if args["verbose"]:
                print("[{} | INFO] png file is being written to {}".format(datetime.datetime.now().time(), png_file))

            # free arguments for a new video
            args["json"] = None
            args["barcode"] = None


if __name__ == "__main__":
    main()

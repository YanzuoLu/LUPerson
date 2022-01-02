import argparse
import os
import pickle

import cv2
from tqdm import tqdm
from yt_dlp import YoutubeDL

def extract_person(dets_dir, save_dir, save_name):
    dets_path = os.path.join(dets_dir, save_name + ".pkl")
    with open(dets_path, "rb") as f:
        dets = pickle.load(f)

    video_path = None
    for root, dirs, files in os.walk(save_dir):
        for file in files:
            if file.split('.')[0] == save_name:
                video_path = os.path.join(root, file)
                break
    if video_path is None:
        print(f"***** [Warning] video {save_name} download failed *****")
        return None
    
    vid = save_name.split('+')[2]
    cap = cv2.VideoCapture(video_path)
    frame_ids = sorted(dets.keys())
    for frame_id in frame_ids:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id - 1)
        ret, image = cap.read()
        if not ret:
            print(f'***** [Warniing] video: {save_name} corrupt at frame: {frame_id - 1} *****')
            continue
        for det in dets[frame_id]:
            obj_idx_at_ori_image = det[0]
            bbox = det[1]["bbox"].round().astype(int)
            img = image[bbox[1]:bbox[3], bbox[0]:bbox[2], :]
            img_name = f"{vid}_{frame_id:08d}_{obj_idx_at_ori_image:04d}.jpg"
            img_path = os.path.join(save_dir, img_name)
            if not os.path.exists(img_path):
                try:
                    cv2.imwrite(img_path, img)
                except:
                    print(f"***** [warning] video {save_name} imwrite failure *****")

    return video_path

def download_video(vid, save_dir, save_name):
    url = "https://www.youtube.com/watch?v=" + vid
    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=?720][filesize<=500M]/best[height<=?720][filesize<=500M]",
        "paths": {"home": save_dir},
        "outtmpl": "{}.%(ext)s".format(save_name), 
        "quiet": True,
        "noprogress": True
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except:
            return

def parse_args():
    parser = argparse.ArgumentParser(description="download luperson raw videos and extract person")
    parser.add_argument("-v", "--vname_file", type=str, default="vnames.txt")
    parser.add_argument("-d", "--dets_dir", type=str, default="dets")
    parser.add_argument("-s", "--save_dir", type=str, default="LUPerson")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    if not os.path.isfile(args.vname_file):
        raise IOError("video name records file does not exist")
    if not os.path.exists(args.dets_dir):
        raise IOError("detection file directory does not exist")
    with open(args.vname_file, "r") as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
    
    if os.path.isfile("finished_video.txt"):
        with open("finished_video.txt", "r") as f:
            finished = f.readlines()
            finished = [line.strip() for line in finished]
        for item in finished:
            if item in lines:
                lines.remove(item)

    for item in tqdm(lines):
        country, city, vid = item.split("+")
        save_dir = os.path.join(args.save_dir, country, city)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        download_video(vid, save_dir, item)
        video_path = extract_person(args.dets_dir, save_dir, item)
        if video_path: os.remove(video_path)
        with open("finished_video.txt", "a") as f:
            f.write(item + "\n")

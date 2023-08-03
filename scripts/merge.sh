#!/bin/bash

input_dir=$(echo $1 | sed -E 's/\/$//')

for dir in $(ls $1); do
    top=$input_dir/$dir
    ffmpeg -y -i $top/video_tracked1.mp4 -i $top/speaker1.wav -c:v copy $top/speaker1.mp4 -loglevel fatal
    ffmpeg -y -i $top/video_tracked2.mp4 -i $top/speaker2.wav -c:v copy $top/speaker2.mp4 -loglevel fatal
    echo
done | rye run tqdm --total $(ls $1 | wc -l)
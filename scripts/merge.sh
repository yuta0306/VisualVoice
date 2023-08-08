#!/bin/bash

input_dir=$(echo $1 | sed -E 's/\/$//')

for dir in $(ls $1); do
    top=$input_dir/$dir
    id=1
    for video in $(ls $top/ | grep video_tracked); do
        ffmpeg -y -i $top/$video -i $top/speaker${id}.wav -c:v copy $top/speaker${id}.mp4 -loglevel fatal
        id=$(($id+1))
    done
    echo
done | rye run tqdm --total $(ls $1 | wc -l) >> /dev/null
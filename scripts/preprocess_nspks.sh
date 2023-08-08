#!/bin/bash

input_dir=$(echo $1 | sed -E 's/\/$//')
output_dir=$(echo $2 | sed -E 's/\/$//')
if [ $# -ne 3 ]; then
    echo "Usage: bash scripts/preprocess_nspks.sh input output n_speakers"
    exit 1
fi
n_spks=$(echo "${3}spks")

for filepath in $(ls $1 | grep .mp4); do
    echo "process $filepath"
    temp_filepath=$(echo $filepath | sed 's/.mp4/fps25.mp4/')
    name=$(echo $filepath | sed 's/.mp4//')
    ffmpeg -y -i $input_dir/$filepath -filter:v fps=fps=25 $input_dir/$temp_filepath -loglevel fatal
    mkdir -p $output_dir/$n_spks/$name/
    ffmpeg -y -i $input_dir/$temp_filepath -vn -ar 16000 -ac 1 -ab 192k -f wav $output_dir/$n_spks/$name/$(echo $filepath | sed 's/.mp4/.wav/') -loglevel fatal
    rye run filter --video_input_path $input_dir/$temp_filepath\
        --output_path $output_dir/$n_spks/$name\
        --detect_every_N_frame 8\
        --scalar_face_detection 1.5\
        --number_of_speakers $3\
        --device cuda:0
    if [ $? -ne 0 ]; then
        rm -r $output_dir/$n_spks/$name
    else
        rye run python ./utils/crop_mouth_from_video.py\
            --video-direc $output_dir/$n_spks/$name/faces/\
            --landmark-direc $output_dir/$n_spks/$name/landmark/\
            --save-direc $output_dir/$n_spks/$name/mouthroi/\
            --convert-gray\
            --filename-path $output_dir/$n_spks/$name/filename_input/$name.csv
    fi
    rm $input_dir/$temp_filepath
done
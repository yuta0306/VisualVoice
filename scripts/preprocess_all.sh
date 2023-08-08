#!/bin/bash

input_dir=$(echo $1 | sed -E 's/\/$//')
output_dir=$(echo $2 | sed -E 's/\/$//')

for filepath in $(ls $1 | grep .mp4); do
    echo "process $filepath"
    temp_filepath=$(echo $filepath | sed 's/.mp4/fps25.mp4/')
    name=$(echo $filepath | sed 's/.mp4//')
    mkdir -p $output_dir/2spk/$name
    mkdir -p $output_dir/1spk/$name

    ffmpeg -y -i $input_dir/$filepath -filter:v fps=fps=25 $input_dir/$temp_filepath -loglevel fatal
    ffmpeg -y -i $input_dir/$temp_filepath -vn -ar 16000 -ac 1 -ab 192k -f wav $output_dir/2spk/$name/$(echo $filepath | sed 's/.mp4/.wav/') -loglevel fatal
    echo "filter this data under existance of two speakers"
    rye run filter --video_input_path $input_dir/$temp_filepath\
        --output_path $output_dir/2spk/$name\
        --detect_every_N_frame 8\
        --scalar_face_detection 1.5\
        --number_of_speakers 2\
        --device cuda:0
    if [ $? -ne 0 ]; then
        rm -r $output_dir/2spk/$name
        ffmpeg -y -i $input_dir/$temp_filepath -vn -ar 16000 -ac 1 -ab 192k -f wav $output_dir/1spk/$name/$(echo $filepath | sed 's/.mp4/.wav/') -loglevel fatal
        echo "filter this data under existance of one speaker"
        rye run filter --video_input_path $input_dir/$temp_filepath\
            --output_path $output_dir/1spk/$name\
            --detect_every_N_frame 8\
            --scalar_face_detection 1.5\
            --number_of_speakers 1\
            --device cuda:0
    fi
    if [ $? -ne 0 ]; then
        rm -r $output_dir/1spk/$name/
    fi

    if [ -d $output_dir/2spk/$name ]; then
        rye run python ./utils/crop_mouth_from_video.py\
            --video-direc $output_dir/2spk/$name/faces/\
            --landmark-direc $output_dir/2spk/$name/landmark/\
            --save-direc $output_dir/2spk/$name/mouthroi/\
            --convert-gray\
            --filename-path $output_dir/2spk/$name/filename_input/$name.csv
    elif [ -d $output_dir/1spk/$name ]; then
        rye run python ./utils/crop_mouth_from_video.py\
            --video-direc $output_dir/1spk/$name/faces/\
            --landmark-direc $output_dir/1spk/$name/landmark/\
            --save-direc $output_dir/1spk/$name/mouthroi/\
            --convert-gray\
            --filename-path $output_dir/1spk/$name/filename_input/$name.csv
    fi
    rm $input_dir/$temp_filepath
    echo done!
done
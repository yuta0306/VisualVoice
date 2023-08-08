#!/bin/bash

input_dir=$(echo $1 | sed -E 's/\/$//')

for name in $(ls $1); do
    speakers=$(ls $input_dir/$name/ | grep video_tracked | wc -l)
    rye run python testRealVideo.py \
        --mouthroi_root $input_dir/$name/mouthroi/ \
        --facetrack_root $input_dir/$name/faces/ \
        --audio_path $input_dir/$name/$name.wav \
        --weights_lipreadingnet pretrained_models/lipreading_best.pth \
        --weights_facial pretrained_models/facial_best.pth \
        --weights_unet pretrained_models/unet_best.pth \
        --weights_vocal pretrained_models/vocal_best.pth \
        --lipreading_config_path configs/lrw_snv1x_tcn2x.json \
        --num_frames 64 \
        --audio_length 2.55 \
        --hop_size 160 \
        --window_size 400 \
        --n_fft 512 \
        --unet_output_nc 2 \
        --normalization \
        --visual_feature_type both \
        --identity_feature_dim 128 \
        --audioVisual_feature_dim 1152 \
        --visual_pool maxpool \
        --audio_pool maxpool \
        --compression_type none \
        --reliable_face \
        --audio_normalization \
        --desired_rms 0.7 \
        --number_of_speakers $speakers \
        --mask_clip_threshold 5 \
        --hop_length 2.55 \
        --lipreading_extract_feature \
        --number_of_identity_frames 1 \
        --output_dir_root $input_dir/$name/
    echo "complete $name"
done | rye run tqdm --total $(ls $1 | wc -l)
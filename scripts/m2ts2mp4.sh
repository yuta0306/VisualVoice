#!/bin/bash

input_dir=$(echo $1 | sed -E 's/\/$//')
output_dir=$(echo $2 | sed -E 's/\/$//')
mkdir -p $output_dir
for m2ts in $(ls $1 | grep .m2ts); do
	ffmpeg -y -ss 1 -i $input_dir/$m2ts  $output_dir/$(echo $m2ts | sed -e 's/m2ts/mp4/') -loglevel fatal
	echo
done | rye run tqdm --total $(ls $1 | wc -l)
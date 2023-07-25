#!/bin/bash

for m2ts in $(ls $1 | grep .mp4$); do
	yes | ffmpeg -ss 1 -i $1$m2ts  $2$(echo $m2ts | sed -e 's/m2ts/mp4/')
done

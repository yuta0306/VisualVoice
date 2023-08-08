import argparse
import math
import os
from pathlib import Path

import ffmpeg
from tqdm import tqdm


def split_file(
    filepath: os.PathLike,
    output_dir: os.PathLike,
    duration: int,
    extension: str = "mp4",
    ss: int = 1,
    max_length: int = -1,
):
    filepath = Path(filepath)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    length = math.ceil(float(ffmpeg.probe(filepath)["streams"][0]["duration"]))
    stream_org = ffmpeg.input(filepath)
    if max_length > 0:
        length = max_length
    ranges = [(i, i + duration) for i in range(ss, length, duration)]
    for ss, tt in tqdm(ranges, total=len(list(ranges)), leave=False):
        stream = ffmpeg.output(
            stream_org,
            filename=output_dir
            / f"{filepath.name.removesuffix(filepath.suffix)}_{ss:04d}-{tt:04d}.{extension}",
            ss=ss,
            t=duration,
            f=extension,
            loglevel="fatal",
        )
        ffmpeg.run(
            stream, overwrite_output=True, capture_stdout=True, capture_stderr=True
        )


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", type=str, default=None)
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--duration", type=int, default=7)
    parser.add_argument("--ss", type=int, default=1)
    parser.add_argument("--max_length", type=int, default=-1)
    args = parser.parse_args()

    if args.filepath is None and args.input is None:
        raise ValueError("filepath or input must be path-like string")

    if args.filepath is not None:
        split_file(
            filepath=args.filepath, output_dir=args.output, duration=args.duration
        )
        return

    files = list(Path(args.input).glob("*.mp4"))
    try:
        for filepath in tqdm(files, leave=True):
            split_file(
                filepath=filepath,
                output_dir=args.output,
                duration=args.duration,
                ss=args.ss,
                max_length=args.max_length,
            )
    except KeyboardInterrupt:
        exit(0)

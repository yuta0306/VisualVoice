import argparse
import math
import os
from pathlib import Path

import ffmpeg
import joblib


def split_file(
    filepath: os.PathLike,
    output_dir: os.PathLike,
    duration: int,
    extension: str = "mp4",
):
    filepath = Path(filepath)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    length = math.ceil(float(ffmpeg.probe(filepath)["streams"][0]["duration"]))
    cur = 1
    stream_org = ffmpeg.input(filepath)
    while cur < length:
        ss = cur
        stream = ffmpeg.output(
            stream_org,
            filename=output_dir
            / f"{filepath.name.removesuffix(filepath.suffix)}_{cur:03d}-{cur+duration:03d}.{extension}",
            ss=ss,
            t=duration,
            f=extension,
            loglevel="fatal",
        )
        ffmpeg.run(
            stream, overwrite_output=True, capture_stdout=True, capture_stderr=True
        )
        cur += duration
    return


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", type=str, default=None)
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--duration", type=int, default=7)
    parser.add_argument("--n_jobs", type=int, default=1)
    args = parser.parse_args()

    if args.filepath is None and args.input is None:
        raise ValueError("filepath or input must be path-like string")

    if args.filepath is not None:
        split_file(
            filepath=args.filepath, output_dir=args.output, duration=args.duration
        )
        return

    files = Path(args.input).glob("*.mp4")
    try:
        _ = joblib.Parallel(n_jobs=args.n_jobs)(
            joblib.delayed(split_file)(
                filepath,
                args.output,
                args.duration,
            )
            for filepath in files
        )
    except KeyboardInterrupt:
        exit(0)

# reference: utils/detectFaces.py

import argparse
import shutil
from pathlib import Path
from warnings import simplefilter

import cv2
import face_alignment
import mmcv
import numpy as np
import torch
from facenet_pytorch import MTCNN
from PIL import Image, ImageDraw


def face2head(
    boxes: list[list[float]],
    scale: float = 1.5,
) -> list[list[float]]:
    new_boxes = []
    for box in boxes:
        width = box[2] - box[0]
        height = box[3] - box[1]
        width_center = (box[2] + box[0]) / 2
        height_center = (box[3] + box[1]) / 2
        square_width = int(max(width, height) * scale)
        new_box = [
            width_center - square_width / 2,
            height_center - square_width / 2,
            width_center + square_width / 2,
            height_center + square_width / 2,
        ]
        new_boxes.append(new_box)
    return new_boxes


def bb_intersection_over_union(boxA: list[float], boxB: list[float]) -> float:
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    # compute the area of intersection rectangle
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)
    # return the intersection over union value
    return iou


class FaceDetector(object):
    def __init__(
        self,
        device: str,
        detect_every_N_frame: int = 8,
        number_of_speakers: int = 2,
        scalar_face_detection: float = 1.5,
    ) -> None:
        self.mtcnn = MTCNN(keep_all=True, device=device)
        self.fa = face_alignment.FaceAlignment(
            face_alignment.LandmarksType._2D, flip_input=False
        )

        self.detect_every_N_frame = detect_every_N_frame
        self.number_of_speakers = number_of_speakers
        self.scalar_face_detection = scalar_face_detection

    def _detect_faces(self, frame: Image.Image) -> list[list[float]]:
        # Detect faces
        boxes, _ = self.mtcnn.detect(frame)
        boxes = boxes[: self.number_of_speakers]
        boxes = face2head(boxes, self.scalar_face_detection)
        return boxes

    def _crop(
        self,
        frame: Image.Image,
        boxes: list[list[float]],
        faces_dic: dict[int, list[list[float]]],
        landmarks_dic: dict[int, list[list[float]]],
        boxes_dic: dict[int, list[list[float]]],
        index: int,
    ) -> None:
        for spk, box in enumerate(boxes):
            face = frame.crop((box[0], box[1], box[2], box[3])).resize((224, 224))
            preds = self.fa.get_landmarks(np.array(face))
            if index == 0:
                faces_dic[spk].append(face)
                landmarks_dic[spk].append(preds)
                boxes_dic[spk].append(box)
            else:
                iou_scores = []
                for b_index in range(self.number_of_speakers):
                    last_box = boxes_dic[b_index][-1]
                    iou_score = bb_intersection_over_union(box, last_box)
                    iou_scores.append(iou_score)
                box_index = iou_scores.index(max(iou_scores))
                faces_dic[box_index].append(face)
                landmarks_dic[box_index].append(preds)
                boxes_dic[box_index].append(box)

    def __call__(
        self,
        frames: list[Image.Image],
    ) -> tuple[
        dict[int, list[list[float]]],
        dict[int, list[list[float]]],
        dict[int, list[list[float]]],
    ]:
        landmarks_dic: dict[int, list[list[float]]] = {
            i: [] for i in range(self.number_of_speakers)
        }
        faces_dic: dict[int, list[list[float]]] = {
            i: [] for i in range(self.number_of_speakers)
        }
        boxes_dic: dict[int, list[list[float]]] = {
            i: [] for i in range(self.number_of_speakers)
        }
        for i, frame in enumerate(frames):
            print(f"\rTracking frame: {i + 1} / {len(frames)}", end="")

            if i % self.detect_every_N_frame == 0:
                boxes = self._detect_faces(frame=frame)
            else:
                boxes = [boxes_dic[j][-1] for j in range(self.number_of_speakers)]

            # if there is a lack of detection
            if len(boxes) != self.number_of_speakers:
                boxes = [boxes_dic[j][-1] for j in range(self.number_of_speakers)]

            # crop faces and save landmarks for each speaker
            self._crop(frame, boxes, faces_dic, landmarks_dic, boxes_dic, index=i)

        return faces_dic, landmarks_dic, boxes_dic


def cli():
    simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_input_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--detect_every_N_frame", type=int, default=8)
    parser.add_argument("--scalar_face_detection", type=float, default=1.5)
    parser.add_argument("--number_of_speakers", type=int, default=2)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    video_input_path = Path(args.video_input_path)
    output_path = Path(args.output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    device = args.device
    if "cuda" in args.device and not torch.cuda.is_available():
        device = "cpu"
        print("device is set to `cpu`, because gpu is not available")

    try:
        video = mmcv.VideoReader(video_input_path.as_posix())
    except Exception as e:
        print(e, "in", output_path.as_posix())
        print("delete", output_path.as_posix())
        shutil.rmtree(output_path.as_posix())
        print("deleted", output_path.as_posix())
        return

    print(
        f"Video statistics: WxH = {video.width}x{video.height}, Resolution = {video.resolution}, FPS = {video.fps}"
    )
    frames = [
        Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)) for frame in video
    ]
    print("Number of frames in video: ", len(frames))

    detector = FaceDetector(
        device=device,
        detect_every_N_frame=args.detect_every_N_frame,
        number_of_speakers=args.number_of_speakers,
        scalar_face_detection=args.scalar_face_detection,
    )

    try:
        faces_dic, landmarks_dic, boxes_dic = detector(frames=frames)
    except Exception as e:
        print(e, "in", output_path.as_posix())
        print("delete", output_path.as_posix())
        shutil.rmtree(output_path.as_posix())
        print("deleted", output_path.as_posix())
        return

    try:
        for s in range(args.number_of_speakers):
            frames_tracked = []
            for i, frame in enumerate(frames):
                # Draw faces
                frame_draw = frame.copy()
                draw = ImageDraw.Draw(frame_draw)
                draw.rectangle(boxes_dic[s][i], outline=(255, 0, 0), width=6)
                # Add to frame list
                frames_tracked.append(frame_draw)
            dim = frames_tracked[0].size
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_tracked = cv2.VideoWriter(
                (output_path / f"video_tracked{s + 1}.mp4").as_posix(),
                fourcc,
                25.0,
                dim,
            )
            for frame in frames_tracked:
                video_tracked.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
            video_tracked.release()
    except Exception as e:
        print(e, "in", output_path.as_posix())
        print("delete", output_path.as_posix())
        shutil.rmtree(output_path.as_posix())
        print("deleted", output_path.as_posix())
        return

    # Save landmarks
    try:
        for i in range(args.number_of_speakers):
            (output_path / "landmark").mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                (output_path / "landmark" / f"speaker{i + 1}.npz").as_posix(),
                data=landmarks_dic[i],
            )
            dim = (224, 224)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            (output_path / "faces").mkdir(parents=True, exist_ok=True)
            speaker_video = cv2.VideoWriter(
                (output_path / "faces" / f"speaker{i + 1}.mp4").as_posix(),
                fourcc,
                25.0,
                dim,
            )
            for frame in faces_dic[i]:
                speaker_video.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
            speaker_video.release()
    except Exception as e:
        print(e, "in", output_path.as_posix())
        print("delete", output_path.as_posix())
        shutil.rmtree(output_path.as_posix())
        print("deleted", output_path.as_posix())
        return

    # Output video path
    try:
        if not (output_path / "filename_input").exists():
            (output_path / "filename_input").mkdir(exist_ok=True)
        with open(
            output_path / "filename_input" / f"{output_path.name}.csv", "w"
        ) as csvfile:
            for i in range(args.number_of_speakers):
                csvfile.write("speaker" + str(i + 1) + ",0\n")
    except Exception as e:
        print(e, "in", output_path.as_posix())
        print("delete", output_path.as_posix())
        shutil.rmtree(output_path.as_posix())
        print("deleted", output_path.as_posix())
        return

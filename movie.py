import argparse
from collections import defaultdict
import glob
import logging
from moviepy import (
    Clip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    clips_array,
    concatenate_videoclips,
)


"""
TV resolution: 1920x1080 16:9  4:2.25 5.3:3
Live Photo resolution: 3024x4032 4:3 30fps
iPhone 11 Pro resolution: 4032x3024 4:3
"""
WIDTH = 1920
HEIGHT = 1080
# top L, top R, bottom L, bottom R
X = [0, 1920 / 2, 0, 1920 / 2]
Y = [0, 0, 1080 / 2, 1080 / 2]

FONT_PATH = "/System/Library/Fonts/Supplemental/Verdana.ttf"
DURATION = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def filename_to_clip(filename: str) -> Clip:
    if filename.endswith(".jpg"):
        return ImageClip(filename).with_duration(DURATION).resized(height=HEIGHT / 2)
    if filename.endswith(".mp4"):
        return (
            VideoFileClip(filename).subclipped(0, DURATION).resized(height=HEIGHT / 2)
        )
    return None


def create_4up(
    input_path: str, filenames: list[str], caption: str
) -> list[CompositeVideoClip]:
    txt_clip = TextClip(
        text=caption,
        font=FONT_PATH,
        font_size=40,
        color="black",
        bg_color="white",
        margin=(20, 20),
        text_align="center",
        duration=DURATION,
    ).with_position("bottom")

    blank = ColorClip((int(WIDTH / 2), int(HEIGHT / 2)), color=(0, 0, 0)).with_duration(
        DURATION
    )
    h_spacer = ColorClip((150, int(HEIGHT / 2)), color=(0, 0, 0)).with_duration(
        DURATION
    )
    # v_spacer = ColorClip((WIDTH, 5), color=(0, 0, 0)).with_duration(DURATION)
    slides = []
    # split filenames into sets of 4
    groups = [filenames[i:i + 4] for i in range(0, len(filenames), 4)]
    log.info(f"{caption}\t{len(filenames)} files on {len(groups)} slides")
    count = 0
    prefix = input_path if input_path.endswith("/") else input_path + "/"
    for group_idx, group in enumerate(groups):
        log.info(f"{count} / {len(filenames)}")
        log.info(f"slide {group_idx+1}\t{len(group)} files")
        count += len(group)
        group.extend([None] * (4 - len(group)))
        (file1, file2, file3, file4) = group
        # 1: full screen
        if file2 is None:
            log.info(f"add {file1} width={WIDTH}")
            slides.append(filename_to_clip(prefix + file1))
            continue
        # 2: one row
        if file3 is None:
            log.info(f"add {file1}, {file2} width={WIDTH/2}")
            clips = [
                [
                    filename_to_clip(prefix + file1),
                    h_spacer,
                    filename_to_clip(prefix + file2),
                ],
                # [v_spacer, h_spacer, v_spacer],
                [blank, h_spacer, blank],
            ]
            print(f"clip sizes {clips[0][0].size}\t{clips[0][1].size}")
        # 3: two rows
        if file3:
            log.info(f"add {file1}, {file2}, {file3} height={HEIGHT/2}")
            clips = [
                [
                    filename_to_clip(prefix + file1),
                    h_spacer,
                    filename_to_clip(prefix + file2),
                ],
                # [v_spacer, h_spacer, v_spacer],
                [filename_to_clip(prefix + file3), h_spacer, blank],
            ]
            print(f"clip sizes {clips[0][0].size}\t{clips[0][1].size}")

        # 4: 2x2 grid
        if file4:
            log.info(f"add {file4} height={HEIGHT/2}")
            clips[-1][-1] = filename_to_clip(prefix + file4)
            print(
                f"clip sizes {clips[0][0].size}\t{clips[0][1].size}\t{clips[-1][0].size}\t{clips[-1][-1].size}"
            )

        log.info(
            f"creating clips array from {[fn.split('/')[-1] for fn in group if fn]}: {clips}"
        )
        # (135, 206, 250)
        slide = clips_array(clips, bg_color=(0, 0, 0))
        # log.info(f"resizing to {WIDTH}")
        # slide = slide.resized(width=WIDTH)
        if group_idx == 0:
            log.info(f"caption {caption}")
            slide = CompositeVideoClip([slide, txt_clip])
        # slide.preview(fps=20)
        log.info(f"done with slide {slide}")
        slides.append(slide)
    print(f"{len(slides)} slides")
    return slides


def load_captions(captions_fn: str) -> dict[str, str]:
    captions = {}
    with open(captions_fn) as f:
        for line in f:
            filename, caption = line.strip().split(",")
            captions[filename] = caption
    return captions


def main(input_path: str, captions_fn: str, limit: int):
    # read captions csv filename, caption
    captions = {}
    if captions_fn:
        captions = load_captions(captions_fn)

    # get all *.{jpg,mp4} files in input_path
    filenames = sorted(
        [fn for fn in glob.glob(f"{input_path}/*") if fn.endswith((".jpg", ".mp4"))]
    )
    filenames = filenames[:limit]
    log.info(f"{len(filenames)} files in {input_path}; {len(captions)} captions")

    # group by caption
    groups: dict[str, list[str]] = defaultdict(list)
    caption = ""
    for full_filename in filenames:
        filename = full_filename.split("/")[-1]
        if captions.get(filename):
            caption = captions[filename]
        groups[caption].append(filename)

    log.info(f"{len(groups)} captions")
    total = 0
    for caption in groups:
        log.info(f"{caption}\t{len(groups[caption])}\t{groups[caption]}")
        total += len(groups[caption])
    log.info(f"{total} files")

    slides = []
    for caption in groups:
        slides.extend(create_4up(input_path, groups[caption], caption))

    log.info(f"concatenating {len(slides)} slides")
    final_clip = concatenate_videoclips(slides, method="compose")
    output_file = "output.mp4"
    log.info(f"writing to {output_file}")
    final_clip.write_videofile(output_file, fps=30, audio=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=str)
    # file containing lines: filename caption
    parser.add_argument("--captions", type=str)
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    _captions_fn = args.captions or args.input_path + "/captions.txt"
    main(args.input_path, _captions_fn, args.limit)

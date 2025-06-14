"""
Re-encode mov in current directory to mp4, dropping audio.
"""

import glob
import subprocess


def main():
    files = sorted(glob.glob("*.mov"))
    for idx, file_path in enumerate(files):
        fn = file_path.split("/")[-1]  # IMG_3417.mov
        out_fn = fn.replace(".mov", ".mp4")
        # -i input file
        # -an drop audio track
        # -vcodec h264 use H.264 encoding
        # -s target image size
        # -y overwrite destination file
        command = ["ffmpeg", "-i", file_path, "-an"] + [
            out_fn,
            "-y",
            "-loglevel",
            "error",
        ]
        print(" ".join(command))
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        print(process.stdout)


if __name__ == "__main__":
    main()

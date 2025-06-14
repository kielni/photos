import argparse
import glob


def main(prefix: str):
    filenames = sorted(glob.glob(f"{prefix}/*.jpg") + glob.glob(f"{prefix}/*.mp4"))
    for fn in filenames:
        if "jpg" in fn:
            print(
                f"""<div class="carousel-item">
  <img src="{fn}" class="d-block w-100">
</div>
"""
            )
        if "mp4" in fn:
            print(
                f"""<div class="carousel-item">
  <div class="embed-responsive embed-responsive-16by9">
    <video loop muted playsinline autoplay class="embed-responsive-item">
      <source src="{fn}">
    </video>
  </div>
</div>
"""
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str)
    args = parser.parse_args()
    main(args.path)

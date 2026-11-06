"""PNG-Master (2160x2700) -> Instagram-JPEG (1080x1350, sRGB, progressiv)."""
import glob
import os
import sys

from PIL import Image

SIZE = (1080, 1350)
BASE = "/home/mrjaws/monatsmenue/dist/social/pre-launch"


def convert(png_path: str) -> str:
    out_dir = os.path.join(os.path.dirname(os.path.dirname(png_path)), "jpg")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(png_path))[0] + ".jpg")
    with Image.open(png_path) as im:
        im = im.convert("RGB")
        if im.size != SIZE:
            im = im.resize(SIZE, Image.LANCZOS)
        im.save(out, "JPEG", quality=92, optimize=True, progressive=True, subsampling=1)
    return out


def main() -> int:
    total = 0
    for png in sorted(glob.glob(os.path.join(BASE, "*", "png", "*.png"))):
        jpg = convert(png)
        total += 1
        print(f"  {os.path.relpath(jpg, BASE):34s} {os.path.getsize(jpg) // 1024}KB")
    print(f"\n{total} JPEG geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())

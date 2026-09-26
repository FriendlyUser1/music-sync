#!/usr/bin/python3
# human written

from pathlib import Path
import sys
import subprocess
import argparse

"""
music sync

for each directory in flac library:
	make mp3_dir by removing any " [FLAC]"
	if mp3_dir exists, skip
	run flac2mp3_bin --preset=320 --processes=processes --copyfiles flac_dir mp3_dir
 
optionally delete cd-rip related files
optionally delete cover images
"""


def run_find(extensions: list[str], dir: Path, delete: bool) -> tuple[bool, str]:
    args = ["find", str(dir), "-type", "f", "("]

    for ext in extensions:
        if ext != extensions[0]:
            args.append("-o")
        args.append("-iname")
        args.append(f"*.{ext}")

    args.append(")")

    if delete:
        args.append("-delete")

    find_process = subprocess.run(args, capture_output=True, text=True)

    if find_process.returncode == 0:
        return (True, find_process.stdout)
    else:
        return (False, find_process.stderr)


def main(
    flac_library: Path,
    mp3_library: Path,
    flac2mp3_bin: Path,
    processes: int,
    delete_extra: bool | None,
    delete_covers: bool | None,
    ignore: list[str] | None,
    parser: argparse.ArgumentParser,
):

    if not flac_library.is_dir() or not flac2mp3_bin.is_file():
        parser.error("The flac library and flac2mp3 binary must exist.")
        parser.print_usage()
        sys.exit(1)

    try:
        if not mp3_library.exists():
            mp3_library.mkdir(parents=True)
    except OSError:
        parser.error(
            "Could not create mp3 library, please try again or choose a different path."
        )
        sys.exit(1)

    flac_dir_list = [x for x in flac_library.iterdir() if x.is_dir()]

    # create mp3 directory name and transcode
    for flac_dir in flac_dir_list:
        if ignore and flac_dir.name in ignore:
            continue

        mp3_dir = mp3_library / flac_dir.name.replace(" [FLAC]", "")
        mp3_dir_alt = mp3_library / flac_dir.name.replace("FLAC", "320")

        if mp3_dir.exists() or mp3_dir_alt.exists():
            continue

        print(f"Transcoding {mp3_dir.name}...")
        subprocess.run(
            [
                flac2mp3_bin,
                "--preset=320",
                f"--processes={processes}",
                "--copyfiles",
                flac_dir,
                mp3_dir,
            ]
        )

    if delete_extra:
        success, output = run_find(["log", "cue", "m3u", "toc"], mp3_library, False)

        if not success:
            parser.error(f"Problem finding extra files:\n{output}")

        if success and output != "":
            success, output = run_find(["log", "cue", "m3u", "toc"], mp3_library, True)

            if success:
                print("Successfully deleted extra files.")
            else:
                parser.error(f"Could not delete extra files:\n{output}")

    if delete_covers:
        success, output = run_find(["jpg", "jpeg", "png"], mp3_library, False)

        if not success:
            parser.error(f"Problem finding cover images:\n{output}")

        if success and output != "":
            success, output = run_find(["jpg", "jpeg", "png"], mp3_library, False)

            if success:
                print("Successfully deleted cover images.")
            else:
                parser.error(f"Could not delete cover images:\n{output}")


if __name__ == "__main__":
    nproc = int(subprocess.run(["nproc"], stdout=subprocess.PIPE, text=True).stdout)

    parser = argparse.ArgumentParser(
        prog="music sync", description="sync flac to mp3 library"
    )
    parser.add_argument("flac_library", help="Path to flac music library")
    parser.add_argument(
        "mp3_library",
        help="Path to mp3 music library, will be created if not existing",
    )
    parser.add_argument(
        "flac2mp3_bin",
        help="Path to flac2mp3 binary, download at https://github.com/robinbowes/flac2mp3/",
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        default=nproc,
        help="Number of concurrent transcoding processes, defaults to running nproc",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        action="append",
        help="Ignore folders in the flac library, use one option per string",
    )
    parser.add_argument(
        "--delete-extra",
        action="store_true",
        help="Delete .cue, .log, .m3u and .toc files in the mp3 library",
    )
    parser.add_argument(
        "--delete-covers",
        action="store_true",
        help="Delete all .jpg, .jpeg and .png files in the mp3 library",
    )
    args = parser.parse_args()

    main(
        Path(args.flac_library),
        Path(args.mp3_library),
        Path(args.flac2mp3_bin),
        args.processes,
        args.delete_extra,
        args.delete_covers,
        args.ignore,
        parser,
    )

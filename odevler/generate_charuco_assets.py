from pathlib import Path

import cv2


def write_png(target: Path, image) -> None:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError(f"PNG encoding failed for {target}")
    target.write_bytes(encoded.tobytes())


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    markers_dir = base_dir / "ocr_assets" / "markers"
    markers_dir.mkdir(parents=True, exist_ok=True)

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    for marker_id in range(4):
        marker = cv2.aruco.generateImageMarker(dictionary, marker_id, 600)
        write_png(markers_dir / f"aruco_{marker_id:02d}.png", marker)

    board = cv2.aruco.CharucoBoard((5, 7), 0.04, 0.03, dictionary)
    board_image = board.generateImage((1800, 2400), marginSize=80, borderBits=1)
    write_png(markers_dir / "charuco_board.png", board_image)

    print(f"OCR assets written to: {markers_dir}")


if __name__ == "__main__":
    main()

"""
Windows Screen Region Capture Tool
===================================
마우스 드래그로 화면 영역을 선택하여 캡처하는 Windows 데스크톱 도구.
캡처된 이미지는 captures/ 디렉토리에 저장됩니다.

사용법: python screen_capture.py
"""

import os
import sys
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import mss
from PIL import Image


CAPTURES_DIR = Path(__file__).parent / "captures"


class RegionSelector:
    """풀스크린 반투명 오버레이에서 마우스 드래그로 영역을 선택합니다."""

    def __init__(self):
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.rect_id = None
        self.selected = False

        self.root = tk.Tk()
        self.root.title("Screen Capture - 영역을 드래그하세요")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.configure(cursor="crosshair", bg="gray")

        self.canvas = tk.Canvas(
            self.root, highlightthickness=0, bg="gray"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Escape>", self._on_escape)

    def _on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=2,
        )

    def _on_drag(self, event):
        if self.rect_id:
            x0 = self.start_x - self.root.winfo_rootx()
            y0 = self.start_y - self.root.winfo_rooty()
            self.canvas.coords(self.rect_id, x0, y0, event.x, event.y)

    def _on_release(self, event):
        self.end_x = event.x_root
        self.end_y = event.y_root
        self.selected = True
        self.root.quit()

    def _on_escape(self, event):
        self.selected = False
        self.root.quit()

    def run(self) -> tuple[int, int, int, int] | None:
        """오버레이를 표시하고 사용자가 영역을 선택할 때까지 대기합니다.
        선택 완료 시 (left, top, right, bottom) 반환, 취소 시 None 반환.
        """
        self.root.mainloop()
        self.root.destroy()

        if not self.selected:
            return None

        left = min(self.start_x, self.end_x)
        top = min(self.start_y, self.end_y)
        right = max(self.start_x, self.end_x)
        bottom = max(self.start_y, self.end_y)

        if right - left < 5 or bottom - top < 5:
            print("선택 영역이 너무 작습니다.")
            return None

        return (left, top, right, bottom)


def capture_region(bbox: tuple[int, int, int, int]) -> Image.Image:
    """mss를 사용하여 화면의 지정 영역을 캡처합니다."""
    left, top, right, bottom = bbox
    monitor = {
        "left": left,
        "top": top,
        "width": right - left,
        "height": bottom - top,
    }
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")


def save_capture(image: Image.Image) -> Path:
    """캡처 이미지를 타임스탬프 파일명으로 저장합니다."""
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = CAPTURES_DIR / f"capture_{timestamp}.png"
    image.save(filepath, "PNG")
    return filepath


def main():
    print("화면 캡처 도구를 시작합니다.")
    print("마우스로 캡처할 영역을 드래그하세요. ESC로 취소합니다.")

    selector = RegionSelector()
    bbox = selector.run()

    if bbox is None:
        print("캡처가 취소되었습니다.")
        sys.exit(0)

    # 오버레이가 완전히 사라진 후 캡처
    time.sleep(0.3)

    image = capture_region(bbox)
    filepath = save_capture(image)
    print(f"캡처 완료: {filepath}")


if __name__ == "__main__":
    main()

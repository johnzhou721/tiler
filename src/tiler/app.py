"""
An app that makes printables with multiple copies of text or image.
"""

import os
# If window is very wide we might be a bit cooked...
os.environ["QT_IMAGEIO_MAXALLOC"] = "1024"

import toga
import togax_frost
import PIL.Image
import asyncio
from toga.style.pack import COLUMN, ROW
from contextlib import contextmanager

LETTER_WIDTH = 5100
LETTER_HEIGHT = 6600
DISPLAY_MARGIN = 10

def center_crop(img: PIL.Image.Image, crop_width: int, crop_height: int) -> PIL.Image.Image:
    width, height = img.size

    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    right = left + crop_width
    bottom = top + crop_height

    return img.crop((left, top, right, bottom))

class Tiler(toga.App):
    def startup(self):
        main_box = toga.Column(flex=1)
        self.canvas_box = toga.Row(flex=2.5, background_color="#F7F3EB")
        control_box = toga.Row(flex=1)
        main_box.add(self.canvas_box)
        main_box.add(control_box)
        self.canvas = togax_frost.RenderCanvas(flex=1)
        self.canvas_width = 0
        self.canvas_height = 0
        self.paper_width = LETTER_WIDTH
        self.paper_height = LETTER_HEIGHT
        self.layout_padding_top = 150 # Placeholder
        self.layout_padding_bottom = 200 # Placeholder
        self.layout_padding_left = 250 # Placeholder
        self.layout_padding_right = 300 # Placeholder
        self.canvas_box.add(self.canvas)
        self.canvas.on_resize = self.canvas_on_resize
        self._is_exporting = False
        self._suppress_resize = False

        self.export_button = toga.Button("Export image", on_press=self.on_export)
        control_box.add(self.export_button)


        # Enforces the minimum height and width of the window by using invisible boxes
        enforce_box = toga.Row(flex=1)
        enforce_box.add(toga.Column(height=715))
        enforce_box2 = toga.Column(flex=1)
        enforce_box2.add(toga.Column(width=400))
        enforce_box2.add(main_box)
        enforce_box.add(enforce_box2)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = enforce_box
        self.main_window.show()

    def on_export(self, button):
        margin_horizontal, margin_vertical, scale = self.compute_paper_frame(border=False)
        width, height = self.canvas_width / scale, self.canvas_height / scale
        with self.sans_redraw():
            self.canvas_draw(border=False)
        print(width, height)
        img = self.canvas.as_image(
            size=(width, height),
            format=PIL.Image.Image,
        )
        with self.sans_redraw():
            self.canvas_draw()
        self.canvas.redraw()
        crop_width, crop_height = self.paper_width, self.paper_height
        print(crop_width, crop_height)
        img = center_crop(img, crop_width, crop_height)
        img.save("/home/johnzhou/test112233.png")

    @contextmanager
    def sans_redraw(self):
        def auxillary_handler():
            pass
        canvas_redraw = self.canvas.redraw
        self.canvas.redraw = auxillary_handler
        yield
        self.canvas.redraw = canvas_redraw

    def compute_paper_frame(self, border=True):
        if border:
            drawable_width, drawable_height = self.canvas_width - 2 * DISPLAY_MARGIN, self.canvas_height - 2 * DISPLAY_MARGIN
        else:
            drawable_width, drawable_height = self.canvas_width, self.canvas_height
        width_scale, height_scale = drawable_width / self.paper_width, drawable_height / self.paper_height
        scale = min(width_scale, height_scale)
        display_width, display_height = scale * self.paper_width, scale * self.paper_height
        margin_horizontal, margin_vertical = (self.canvas_width - display_width) / 2, (self.canvas_height - display_height) / 2
        return margin_horizontal, margin_vertical, scale

    def canvas_draw(self, border=True):
        left, top, scale = self.compute_paper_frame(border=border)
        # print("CANVAS DRAW", left, top, scale)

        self.canvas.root_state.drawing_actions.clear()

        with self.canvas.state():
            self.canvas.translate(left, top)
            self.canvas.scale(scale, scale)

            width, height = self.paper_width, self.paper_height

            if border:
                with self.canvas.stroke(line_width=25):
                    self.canvas.move_to(0, 0)
                    self.canvas.line_to(width, 0)
                    self.canvas.line_to(width, height)
                    self.canvas.line_to(0, height)
                    self.canvas.line_to(0, 0)
                    self.canvas.close_path()

            with self.canvas.state():
                client_width = width - self.layout_padding_left - self.layout_padding_right
                client_height = height - self.layout_padding_top - self.layout_padding_bottom

                self.canvas.translate(
                    self.layout_padding_left,
                    self.layout_padding_top
                )

                with self.canvas.stroke(line_width=15):
                    self.canvas.move_to(0, 0)
                    self.canvas.line_to(client_width, 0)
                    self.canvas.line_to(client_width, client_height)
                    self.canvas.line_to(0, client_height)
                    self.canvas.line_to(0, 0)
                    self.canvas.close_path()

    def canvas_on_resize(self, widget, width, height, **kwargs):
        self.canvas_width = width
        self.canvas_height = height
        with self.sans_redraw():
            self.canvas_draw()
        self.canvas.redraw()

def main():
    return Tiler()

"""
An app that makes printables with multiple copies of text or image.
"""

import toga
import togax_frost
import PIL.Image
import asyncio
from toga.style.pack import COLUMN, ROW
from contextlib import contextmanager

LETTER_WIDTH = 5100
LETTER_HEIGHT = 6600
DISPLAY_MARGIN = 10

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
        self._before_width = 0
        self._before_height = 0

        self._last_width = 0
        self._last_height = 0

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
        self._is_exporting = True
        self._before_width = self.canvas_width
        self._before_height = self.canvas_height
        self.canvas_box.width = self.canvas_width
        self.canvas_box.height = self.canvas_height
        with self.canvas.style.batch_apply():
            self.canvas.height = self.paper_height
            self.canvas.width = self.paper_width
            # Make it so that the width/height is 0 so the min window size
            # does not change, haha
            self.canvas.margin_bottom = -self.paper_height
            self.canvas.margin_right = -self.paper_width

    @contextmanager
    def sans_redraw(self):
        def auxillary_handler():
            pass
        canvas_redraw = self.canvas.redraw
        self.canvas.redraw = auxillary_handler
        yield
        self.canvas.redraw = canvas_redraw

    def compute_paper_frame(self):
        drawable_width, drawable_height = self.canvas_width - 2 * DISPLAY_MARGIN, self.canvas_height - 2 * DISPLAY_MARGIN
        width_scale, height_scale = drawable_width / self.paper_width, drawable_height / self.paper_height
        scale = min(width_scale, height_scale)
        display_width, display_height = scale * self.paper_width, scale * self.paper_height
        margin_horizontal, margin_vertical = (self.canvas_width - display_width) / 2, (self.canvas_height - display_height) / 2
        return margin_horizontal, margin_vertical, scale

    def canvas_draw(self):
        left, top, scale = self.compute_paper_frame()
        # print("CANVAS DRAW", left, top, scale)

        with self.canvas.state():
            self.canvas.translate(left, top)
            self.canvas.scale(scale, scale)

            width, height = self.paper_width, self.paper_height

            with self.canvas.stroke(line_width=40):
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

    @contextmanager
    def suppress_resizes(self):
        self._suppress_resize = True
        yield
        self._suppress_resize = False

    async def canvas_on_resize(self, widget, width, height, **kwargs):
        # print(self._last_width, self._last_height, "to", width, height)
        # await asyncio.sleep(0)
        if (self._last_width, self._last_height) != (width, height):
            self._last_width, self._last_height = width, height
            self.canvas_on_actual_resize(widget, width, height, **kwargs)

    def canvas_on_actual_resize(self, widget, width, height, **kwargs):
        if not self._suppress_resize:
            # print("On resize call", width, height)
            if self._is_exporting:
                with self.suppress_resizes():
                    self.canvas_width = width
                    self.canvas_height = height
                    # print(self.canvas_width, self.canvas_height)
                    with self.sans_redraw():
                        self.canvas.root_state.drawing_actions.clear()
                        self.canvas_draw()
                    if toga.backend == "toga_cocoa":
                        self.canvas._impl.native.layoutSubtreeIfNeeded()
                    self.canvas.as_image().as_format(PIL.Image.Image).save("/Users/johnzhou/test112233.png")
                    # print("Exported image")
                    # The below immediately resizes so... is_exporting is set to False before this
                    # with self.canvas.style.batch_apply():
                    with self.canvas.style.batch_apply():
                        del self.canvas.width
                        del self.canvas.height
                        del self.canvas.margin_right
                        del self.canvas.margin_bottom
                    # print("before context exit")
                    del self.canvas_box.width
                    del self.canvas_box.height
                    # print("Finished resetting properties")
                    self._is_exporting = False

                    # Render with width/height before
                    self.canvas_width = self._before_width
                    self.canvas_height = self._before_height
                    # print(self.canvas_width, self.canvas_height)
                    with self.sans_redraw():
                        self.canvas.root_state.drawing_actions.clear()
                        self.canvas_draw()
                    # print("Redrawn")
                    self.canvas.redraw()
                    
            else:
                self.canvas_width = width
                self.canvas_height = height
                # print(self.canvas_width, self.canvas_height)
                with self.sans_redraw():
                    self.canvas.root_state.drawing_actions.clear()
                    self.canvas_draw()
                self.canvas.redraw()

def main():
    return Tiler()

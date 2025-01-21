import flet
import time
import win32com.client
from io import BytesIO
import pythoncom
from PIL import Image as PILImage
from threading import Thread
from flet import ElevatedButton, Row, Column, Page, Image, Icon, icons, TextButton
import base64
import threading
import io
import numpy as np

# Callback function placeholder
signature_callback = None
update_signature_running = False
update_signature_thread = None

# Global event for synchronization
signature_captured_event = threading.Event()

# Global reference for the signature image control in Flet
sigplus = None  # Global reference to the Topaz device


def update_signature(page, image_widget):
    global sigplus, update_signature_running
    while update_signature_running:
        if sigplus and sigplus.TabletConnectQuery():
            try:
                # Write to bitmap buffer and retrieve bytes
                sigplus.BitMapBufferWrite()
                byte_value = sigplus.GetBitmapBufferBytes()
                sigplus.BitMapBufferClose()

                if byte_value is None:
                    raise ValueError("Signature data is None")
                    continue

                image_widget.src_base64 = base64.b64encode(byte_value).decode("utf-8")
                page.update()

            except Exception as e:
                print("Error in signature capture or processing:", e)

        time.sleep(0.1)  # Adjust as needed


def clear_signature():
    global sigplus
    sigplus.ClearTablet()


def accept_signature(page, incarcerated, assets, current_time):
    global sigplus, signature_callback
    try:
        # Write to bitmap buffer and retrieve bytes
        sigplus.BitMapBufferWrite()
        byte_value = sigplus.GetBitmapBufferBytes()
        sigplus.BitMapBufferClose()

        if byte_value is None:
            raise ValueError("Signature data is None")

        # Convert bytes to a PIL image
        image = PILImage.open(io.BytesIO(byte_value))

        # Convert image to RGBA if it's not already
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Process image to make white (and near-white) pixels transparent
        data = np.array(image)  # Convert to numpy array
        red, green, blue, alpha = data.T  # Transpose to get channels
        # Replace white and near-white pixels with transparent
        white_areas = (red > 200) & (blue > 200) & (green > 200)
        data[..., :-1][white_areas.T] = (
            255,
            255,
            255,
        )  # Set color to white, keeping format
        data[..., -1][white_areas.T] = 0  # Make transparent

        # Convert numpy array back to PIL image
        processed_image = PILImage.fromarray(data)

        # Convert processed image back to bytes
        byte_arr = io.BytesIO()
        processed_image.save(byte_arr, format="PNG")
        processed_signature_data = byte_arr.getvalue()

        # Convert to base64
        signature_data = base64.b64encode(processed_signature_data).decode("utf-8")

        if signature_callback:
            signature_callback(signature_data, incarcerated, assets, current_time)

    except Exception as e:
        print("Error saving signature:", e)

    cancel_signature(page)


def cancel_signature(page: Page):
    global sigplus, update_signature_running, update_signature_thread
    update_signature_running = False
    if update_signature_thread.is_alive():
        update_signature_thread.join()
    page.window_destroy()
    signature_captured_event.set()


def main(page: Page, callback, incarcerated, assets, current_time):
    global sigplus, signature_callback, update_signature_running, update_signature_thread
    signature_callback = (
        lambda signature_data, incarcerated, assets, current_time: callback(
            signature_data, incarcerated, assets, current_time
        )
    )
    update_signature_running = True

    page.window_height = 320
    page.window_center()
    page.title = "Signature Capture"
    page.window_always_on_top = True
    page.window_skip_task_bar = True
    page.window_resizable = False
    page.window_frameless = True
    page.window_title_bar_hidden = True
    page.window_maximizable = False
    page.window_minimizable = False
    page.window_focused = True

    pythoncom.CoInitialize()

    if not sigplus:
        sigplus = win32com.client.Dispatch("SigPlus.SigPlusCtrl.1")
    sigplus.InitSigPlus()
    sigplus.AutoKeyStart()
    sigplus.AutoKeyFinish()
    sigplus.SigCompressionMode = 1

    # Set properties for bitmap
    sigplus.ImageFileFormat = 0
    sigplus.ImageXSize = 1500
    sigplus.ImageYSize = 500
    sigplus.ImagePenWidth = 10
    sigplus.JustifyMode = 5

    signature_image = Image(height=300, width=900, src="temp.png")

    cancel_button = TextButton(
        width=150,
        height=100,
        content=Icon(name=icons.CANCEL_OUTLINED, color="red", size=50),
        on_click=lambda e: cancel_signature(page),
    )
    clear_button = TextButton(
        width=150,
        height=100,
        content=Icon(name=icons.CIRCLE_OUTLINED, color="yellow", size=50),
        on_click=lambda e: clear_signature(),
    )
    accept_button = TextButton(
        width=150,
        height=100,
        content=Icon(name=icons.CHECK_CIRCLE_OUTLINED, color="green", size=50),
        on_click=lambda e: accept_signature(page, incarcerated, assets, current_time),
    )

    buttons_column = Column(
        [cancel_button, clear_button, accept_button], alignment="spaceEvenly"
    )
    main_row = Row([signature_image, buttons_column], alignment="spaceBetween")
    page.add(main_row)

    update_signature_thread = Thread(
        target=update_signature,
        args=(
            page,
            signature_image,
        ),
        daemon=True,
    )
    update_signature_thread.start()


def launch(callback, incarcerated, assets, current_time):
    flet.app(
        target=lambda page: main(page, callback, incarcerated, assets, current_time)
    )

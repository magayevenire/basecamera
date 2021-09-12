import time
import logging
from functools import partial
from enum import Enum

from kivymd.app import App
from kivy.animation import Animation
from kivy import platform
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import (
    ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, OptionProperty)
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo, Callback, Rectangle
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.stencilview import StencilView
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen

from kivy.uix.image import  Image 


logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

from camera2 import PyCameraInterface

from android.permissions import request_permission, check_permission, Permission

class PermissionRequestStates(Enum):
    UNKNOWN = "UNKNOWN"
    HAVE_PERMISSION = "HAVE_PERMISSION"
    DO_NOT_HAVE_PERMISSION = "DO_NOT_HAVE_PERMISSION"
    AWAITING_REQUEST_RESPONSE = "AWAITING_REQUEST_RESPONSE"


class KivyCamera(Image):



    def __init__(self, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
 
        # self.allow_stretch = True
        self.app = App.get_running_app()
        # self.oroot = self.app.getScreen('enregistrement')
        # print(self.parent)
        self.fps =30




    def startUpdate(self):
        self.event = Clock.schedule_interval(self.actualProgram , 1.0 / self.fps)

        pass




    def stopUpdate(self):
        self.event.cancel()

        pass







    def update(self, dt):
        print(self.app.texture.pixels)
        # ret, img ,imgS = self.getImage()
        # if ret:

        #     self.displayImage(img)


class MenuScreen(Screen):
    pass

class FaceAndTempScreen(Screen):

    def __init__(self, **kwargs):
        
        super(FaceAndTempScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()




    def myBack(self):
        self.manager.current ="menu"
        # sm.current = "menu"
    def on_pre_enter(self):
        pass
        
        # self.app.startCam()




class CameraApp(App):
    texture = ObjectProperty(None, allownone=True)
    camera_resolution = ListProperty([4032, 3016])
    # camera_resolution = ListProperty([1920, 1080])

    current_camera = ObjectProperty(None, allownone=True)

    cameras_to_use = ListProperty()

    camera_permission_state = OptionProperty(
        PermissionRequestStates.UNKNOWN,
        options=[PermissionRequestStates.UNKNOWN,
                 PermissionRequestStates.HAVE_PERMISSION,
                 PermissionRequestStates.DO_NOT_HAVE_PERMISSION,
                 PermissionRequestStates.AWAITING_REQUEST_RESPONSE])
    _camera_permission_state_string = StringProperty("UNKNOWN")

    def on_camera_permission_state(self, instance, state):
        self._camera_permission_state_string = state.value


    def build(self):

        self.theme_cls.primary_palette = "Blue"  # "Purple", "Red" Green
        # self.theme_cls.theme_style = "Dark"
        self.camera_interface = PyCameraInterface()


        self.debug_print_camera_info()

        self.inspect_cameras()

        self.restart_stream()
        self.screen = Builder.load_file('androidcamera.kv')
        Clock.schedule_interval(self.update, 0)
        return self.screen




    def inspect_cameras(self):
        cameras = self.camera_interface.cameras

        for camera in cameras:
            if camera.facing == "BACK":
                self.cameras_to_use.append(camera)
        for camera in cameras:
            if camera.facing == "FRONT":
                self.cameras_to_use.append(camera)

    def rotate_cameras(self):
        self.ensure_camera_closed()
        self.cameras_to_use = self.cameras_to_use[1:] + [self.cameras_to_use[0]]
        self.attempt_stream_camera(self.cameras_to_use[0])

    def restart_stream(self):
        self.ensure_camera_closed()
        Clock.schedule_once(self._restart_stream, 0)

    def _restart_stream(self, dt):
        logger.info("On restart, state is {}".format(self.camera_permission_state))
        if self.camera_permission_state in (PermissionRequestStates.UNKNOWN, PermissionRequestStates.HAVE_PERMISSION):
            self.attempt_stream_camera(self.cameras_to_use[1])
        else:
            logger.warning(
                "Did not attempt to restart camera stream as state is {}".format(self.camera_permission_state))

    def debug_print_camera_info(self):
        cameras = self.camera_interface.cameras
        # camera_infos = ["Camera ID {}, facing {}".format(c.camera_id, c.facing) for c in cameras]
        for camera in cameras:
            print("Camera ID {}, facing {}, resolutions {}".format(
                camera.camera_id, camera.facing, camera.supported_resolutions))

    def attempt_stream_camera(self, camera):
        """Start streaming from the given camera, if we have the CAMERA
        permission, otherwise request the permission first.
        """

        if check_permission(Permission.CAMERA):
            self.stream_camera(camera)
        else:
            self.camera_permission_state = PermissionRequestStates.AWAITING_REQUEST_RESPONSE
            request_permission(Permission.CAMERA, partial(self._request_permission_callback, camera))

    def _request_permission_callback(self, camera, permissions, alloweds):
        # Assume  that we  received info  about exactly  1 permission,
        # since we only ever ask for CAMERA
        allowed = alloweds[0]

        if allowed:
            self.camera_permission_state = PermissionRequestStates.HAVE_PERMISSION
            self.stream_camera(camera)
        else:
            self.camera_permission_state = PermissionRequestStates.DO_NOT_HAVE_PERMISSION
            print("PERMISSION FORBIDDEN")

    def stream_camera(self, camera):
        resolution = (3264, 2448)

        self.camera_resolution = resolution
        camera.open(callback=self._stream_camera_open_callback)

    def _stream_camera_open_callback(self, camera, action):
        if action == "OPENED":
            logger.info("Camera opened, preparing to start preview")
            Clock.schedule_once(partial(self._stream_camera_start_preview, camera), 0)
        else:
            logger.info("Ignoring camera event {action}")

    def _stream_camera_start_preview(self, camera, *args):

        self.texture = camera.start_preview(tuple(self.camera_resolution))

        self.current_camera = camera



    def on_texture(self, instance, value):
        print("App texture changed to {}".format(value))
        

    def update(self, dt):
        self.root.canvas.ask_update()
        print(self.texture.pixels)



    

    def ensure_camera_closed(self):
        if self.current_camera is not None:
            self.current_camera.close()
            self.current_camera = None

    def on_pause(self):

        logger.info("Closing camera due to pause")
        self.ensure_camera_closed()

        return super().on_pause()

    def on_resume(self):
        logger.info("Opening camera due to resume")
        self.restart_stream()




if __name__ == "__main__":
    CameraApp().run()

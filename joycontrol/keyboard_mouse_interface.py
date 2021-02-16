import inspect
import logging
import shlex
from selectors import DefaultSelector, EVENT_READ
import sys
import termios

from evdev import InputDevice, ecodes

from joycontrol.controller_state import ControllerState
from joycontrol.transport import NotConnectedError

logger = logging.getLogger(__name__)

class KMI():
    def __init__(self, controller_state: ControllerState):
        mpath = '/dev/input/event6'
        kpath = '/dev/input/event2'
        self.controller_state = controller_state
        self.button_state = controller_state.button_state
        self.lstick_state = controller_state.l_stick_state
        self.axis_state = controller_state.axis_state

        self.mouse = InputDevice(mpath)
        print(self.mouse)
        self.keyboard = InputDevice(kpath)
        print(self.keyboard)
        self.mouse.grab()
        

    async def run(self):
        l = [False]*4
        
        selector = DefaultSelector()
        selector.register(self.mouse, EVENT_READ)
        selector.register(self.keyboard, EVENT_READ)

        while True:
            for key, mask in selector.select(0):
                device = key.fileobj
                for event in device.read():
                    if event is not None:
                        # mouse movement
                        if event.type == ecodes.EV_REL:
                            if event.code == ecodes.REL_X:
                                dx = event.value
                                self.controller_state.axis_state.dx += dx
                            elif event.code == ecodes.REL_Y:
                                dy = event.value
                                self.controller_state.axis_state.dy += dy
                                self.controller_state.axis_state.sum_y += dy
                            
                        # mouse click
                        elif event.type == ecodes.EV_KEY:
                            pushed = True
                            if event.value == 0x01:#key down
                                pushed = True
                            elif event.value == 0x00:
                                pushed = False
                            
                            #left click -> ZR
                            if event.code == ecodes.BTN_LEFT:
                                self.button_state.zr(pushed)
                                #right click -> ZL
                            elif event.code == ecodes.BTN_RIGHT:
                                self.button_state.zl(pushed)
                                #middle click -> Y
                            if event.code == ecodes.BTN_MIDDLE:
                                self.button_state.y(pushed)

                            #WASD -> up, left, right, down
                            if event.code == ecodes.KEY_W:
                                if pushed:
                                    self.lstick_state.set_up()
                                    l[0] = True
                                else:
                                    if l[2]:
                                        self.lstick_state.set_down()
                                    else:
                                        self.lstick_state.set_v(self.lstick_state._calibration.v_center)
                                    l[0] = False
                            elif event.code == ecodes.KEY_A:
                                if pushed:
                                    self.lstick_state.set_left()
                                    l[1] = True
                                else:
                                    if l[3]:
                                        self.lstick_state.set_right()
                                    else:
                                        self.lstick_state.set_h(self.lstick_state._calibration.h_center)
                                    l[1] = False
                            elif event.code == ecodes.KEY_S:
                                if pushed:
                                    self.lstick_state.set_down()
                                    l[2] = True
                                else:
                                    if l[0]:
                                        self.lstick_state.set_up()
                                    else:
                                        self.lstick_state.set_v(self.lstick_state._calibration.v_center)
                                    l[2] = False
                            elif event.code == ecodes.KEY_D:
                                if pushed:
                                    self.lstick_state.set_right()
                                    l[3] = True
                                else:
                                    if l[1]:
                                        self.lstick_state.set_up()
                                    else:
                                        self.lstick_state.set_h(self.lstick_state._calibration.h_center)
                                    l[3] = False

                                #FVE -> a,b,x
                            elif event.code == ecodes.KEY_F:
                                self.button_state.a(pushed)
                            elif event.code == ecodes.KEY_V:
                                self.button_state.b(pushed)
                            elif event.code == ecodes.KEY_E:
                                self.button_state.x(pushed)

                                #TG -> rstick, lstick
                            elif event.code == ecodes.KEY_T:
                                self.button_state.l_stick(pushed)
                            elif event.code == ecodes.KEY_G:
                                self.button_state.r_stick(pushed)
                                #QR -> l,r
                            elif event.code == ecodes.KEY_Q:
                                self.button_state.l(pushed)
                            elif event.code == ecodes.KEY_R:
                                self.button_state.r(pushed)
                            #ZX -> plus, minus
                            elif event.code == ecodes.KEY_Z:
                                self.button_state.minus(pushed)
                            elif event.code == ecodes.KEY_X:
                                self.button_state.plus(pushed)
                            #TAB -> zl
                            elif event.code == ecodes.KEY_TAB:
                                self.button_state.zl(pushed)
                            #SPACE -> b
                            elif event.code == ecodes.KEY_SPACE:
                                self.button_state.b(pushed)
                                #esc -> home
                            elif event.code == ecodes.KEY_ESC:
                                self.button_state.home(pushed)
                                
                            #del -> break
                            elif event.code == ecodes.KEY_DELETE:
                                self.mouse.ungrab()
                                return
                        
                try:
                    await self.controller_state.send()
                except NotConnectedError:
                    logger.info('Connection was lost.')
                    self.mouse.ungrab()
                    return

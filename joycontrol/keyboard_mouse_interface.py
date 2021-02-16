import inspect
import logging
import shlex
import asyncio
import sys
import termios

from evdev import InputDevice, ecodes

from joycontrol.controller_state import ControllerState
from joycontrol.transport import NotConnectedError

logger = logging.getLogger(__name__)

class KMI():
    def __init__(self, controller_state: ControllerState):
        mpath = 'dev/input/event7'
        kpath = 'dev/input/event2'
        self.controller_state = controller_state
        self.button_state = controller_state.button_state
        self.lstick_state = controller_state.l_stick_state
        self.axis_state = controller_state.axis_state

        self.mouse = InputDevice(mpath)
        self.keyboard = InputDevice(kpath)
        self.mouse.grab()

        fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] &= ~termios.ECHO
        
        termios.tcsetattr(fd,termios.TCSANOW,new)
        

    async def run(self):
        while True:
            minput = await self.mouse.async_read()
            kinput = await self.keyboard.async_read()

            # parse mouse event
            if minput is not None:
                # mouse movement
                if event.type == ecodes.EV_REL:
                    if event.code = ecodes.REL_X:
                        dx = event.val
                        self.controller_state.axis_state.dx += dx
                    elif event.code = ecodes.REL_Y:
                        dy = event.val
                        self.controller_state.axis_state.dy += dy
                        self.controller_state.axis_state.sum_y += dy

                # mouse click
                if event.type = ecodes.EV_KEY:
                    push = True
                    if event.val == 0x01:#key down
                        pushed = True
                    elif event.val == 0x00:
                        pushed = False
    
                    #left click -> ZR
                    if event.code == ecode.BTN_LEFT:
                            self.button_state.zr(push)
                    #right click -> ZL
                    elif event.code == ecode.BTN_RIGHT:
                        self.button_state.zl(not push)
                    #middle click -> Y
                    if event.code == ecodes.BTN_MIDDLE:
                        self.button_state.y(push)

            # parse keyboard event
            if kinput is not None:
                # key input
                if event.type == ecodes.EV_KEY:
                    push = True
                    if event.val == 0x01:#key down
                        pushed = True
                    elif event.val == 0x00:
                        pushed = False

                    #WASD -> up, left, right, down
                    if event.code == ecode.KEY_W:
                        self.lstick_state.set_up()
                    elif event.code == ecode.KEY_A:
                        self.lstick_state.set_left()
                    elif event.code == ecode.KEY_S:
                        self.lstick_state.set_right()
                    elif event.code == ecode.KEY_D:
                        self.lstick_state.set_down()

                    #FVE -> a,b,x
                    elif event.code == ecode.KEY_F:
                        self.button_state.a(push)
                    elif event.code == ecode.KEY_V:
                        self.button_state.b(push)
                    elif event.code == ecode.KEY_E:
                        self.button_state.x(push)

                    #TG -> rstick, lstick
                    elif event.code == ecode.KEY_T:
                        self.button_state.sl(push)
                    elif event.code == ecode.KEY_G:
                        self.button_state.sr(push)
                    #QR -> l,r
                    elif event.code == ecode.KEY_Q:
                        self.button_state.l(push)
                    elif event.code == ecode.KEY_R:
                        self.button_state.r(push)
                    #ZX -> plus, minus
                    elif event.code == ecode.KEY_Z:
                        self.button_state.plus(push)
                    elif event.code == ecode.KEY_X:
                        self.button_state.minus(push)
                    #TAB -> zl
                    elif event.code == ecode.KEY_TAB:
                        self.button_state.zl(push)
                    #SPACE -> b
                    elif event.code == ecode.KEY_SPACE:
                        self.button_state.b(push)
                    #esc -> home
                    elif event.code == ecode.KEY_ESC:
                        self.button_state.home(push)

                    #del -> break
                    elif event.code == ecode.KEY_DELETE:
                        self.mouse.ungrab()
                        termios.tcsetattr(sys.stdin.fileno(),termios.TCSANOW,self.old)
                        return
        
            try:
                await self.controller_state.send()
            except NotConnectedError:
                logger.info('Connection was lost.')
                self.mouse.ungrab()
                termios.tcsetattr(sys.stdin.fileno(),termios.TCSANOW,self.old)
                return
# painter class 

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ..IO.representation import *
import ode
from math import sqrt
example, inputs = ("M[" +
        "J[R, color[Green], P[0.0, 0.0], L[ground, link_1]], " +
        "J[R, color[Green], P[12.92, 32.53], L[link_1, link_2]], " +
        "J[R, color[Green], P[73.28, 67.97], L[link_2, link_3]], " +
        "J[R, color[Green], P[33.3, 66.95], L[link_2]], " +
        "J[R, color[Green], P[90.0, 0.0], L[ground, link_3]]" +
        "]", {0: ('ground', 'link_1')})
        
"""
example, inputs = ("M[" +
    "J[R, color[Green], P[0.0, 0.0], L[ground, link_1]], " +
    "J[R, color[Green], P[9.61, 11.52], L[link_1, link_2, link_4]], " +
    "J[R, color[Blue], P[-38.0, -7.8], L[ground, link_3, link_5]], " +
    "J[R, color[Green], P[-35.24, 33.61], L[link_2, link_3]], " +
    "J[R, color[Green], P[-77.75, -2.54], L[link_3, link_6]], " +
    "J[R, color[Green], P[-20.1, -42.79], L[link_4, link_5, link_7]], " +
    "J[R, color[Green], P[-56.05, -35.42], L[link_6, link_7]], " +
    "J[R, color[Green], P[-22.22, -91.74], L[link_7]]" +
    "]", {0: ('ground', 'link_1')})

example, input = ("M[" +
    "J[R, color[Green], P[0.0, 0.0], L[ground, link_1]], " +
    "J[R, color[Green], P[9.61, 11.52], L[link_1, link_2, link_4, link_8, link_10]], " +
    "J[R, color[Blue], P[-38.0, -7.8], L[ground, link_3, link_5]], " +
    "J[R, color[Green], P[-35.24, 33.61], L[link_2, link_3]], " +
    "J[R, color[Green], P[-77.75, -2.54], L[link_3, link_6]], " +
    "J[R, color[Green], P[-20.1, -42.79], L[link_4, link_5, link_7]], " +
    "J[R, color[Green], P[-56.05, -35.42], L[link_6, link_7]], " +
    "J[R, color[Green], P[-22.22, -91.74], L[link_7]], " +
    "J[R, color[Blue], P[38.0, -7.8], L[ground, link_9, link_11]], " +
    "J[R, color[Green], P[56.28, 29.46], L[link_8, link_9]], " +
    "J[R, color[Green], P[75.07, -23.09], L[link_9, link_12]], " +
    "J[R, color[Green], P[31.18, -46.5], L[link_10, link_11, link_13]], " +
    "J[R, color[Green], P[64.84, -61.13], L[link_12, link_13]], " +
    "J[R, color[Green], P[4.79, -87.79], L[link_13]]" +
    "]", {0: ('ground', 'link_1')})
"""

class CanvasPaint(QWidget):
    
    fps = 50
    dt = 0.01
    simcontrol2real = pyqtSignal(str)
    
    def __init__(self, parent = None):
        super(CanvasPaint, self).__init__(parent)
        #self.test()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.vlinks = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.angle = 0
        self.target = 0
        self.zoom = 2
        self.loopFlag = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.timeout.connect(lambda: self.world.step(self.dt)) #sec
        
        self.plotdata = []
        
    def __lenth(self, p1, p2):
        lenth = sqrt((p2[0]-p1[0])*(p2[0]-p1[0])+(p2[1]-p1[1])*(p2[1]-p1[1]))
        return lenth
        
    def __lenthCenter(self, p1, p2):
        return ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, 0)
        
    def __translate23d(self, position):
        return (position[0], position[1], 0)
    
    def loaddata(self, vpoints):
        
        self.world = ode.World()
        self.world.setGravity((0,-9.81, 0))
        #vpoints = parse_vpoints(mechanism)
        
        self.vlinks = {}
        for i, vpoint in enumerate(vpoints):
            for link in vpoint.links:
                if link in self.vlinks:
                    self.vlinks[link].append(i)
                else:
                    self.vlinks[link] = [i]
        
        self.bodies = []
        
        for name in tuple(self.vlinks):
            if name == 'ground':
                continue
            vlink = self.vlinks[name]
            while len(vlink) > 2:
                n = vlink.pop()
                for anchor in vlink[:2]:
                    i = 1
                    while 'link_{}'.format(i) in self.vlinks:
                        i += 1
                    self.vlinks['link_{}'.format(i)] = (anchor, n)
        
        
        for name, vlink in self.vlinks.items():
            #print(name, [(vpoints[i].cx, vpoints[i].cy) for i in vlink])
            if name == 'ground':
                continue
            rad = 0.002
            Mass = 1
            link = ode.Body(self.world)
            M = ode.Mass() # mass parameter
            M.setZero() # init the Mass
            M.setCylinderTotal(Mass, 3, rad, self.__lenth(vpoints[vlink[0]], vpoints[vlink[1]]))
            link.setPosition(self.__lenthCenter(vpoints[vlink[0]], vpoints[vlink[1]]))
            print(vlink)
            self.bodies.append(link)
        
        
        self.joints = []
        for name, vlink in self.vlinks.items():
            link = list(vlink)
            if name == 'ground':
                for p in link:
                    if p in inputs:
                        print("input:", p)
                        j = ode.HingeJoint(self.world)
                        #j.attach(bodies[(vlinks[inputs[p][1]] - {p}).pop()], ode.environment)
                        j.attach(self.bodies[0], ode.environment)
                        j.setAxis((0, 0, 1))
                        j.setAnchor(self.__translate23d(vpoints[vlink[0]]))
                        j.setParam(ode.ParamVel, 2)
                        j.setParam(ode.ParamFMax, 22000)
                    else:
                        print("grounded:", p)
                        j = ode.BallJoint(self.world)
                        j.attach(self.bodies[p], ode.environment)
                        j.setAnchor(self.__translate23d(vpoints[vlink[1]]))
                    self.joints.append(j)
            elif len(link) >= 2:
                print("link:", link[0], link[1])
                j = ode.BallJoint(self.world)
                j.attach(self.bodies[link[0]], self.bodies[link[1]])
                j.setAnchor(self.__translate23d(vpoints[link[0]]))
                self.joints.append(j)

    def testfuc(self):
        for i in range(0, len(self.joints)):
            print(type(self.joints[i].getBody()))
    
    def setTimer(self, count):
        if count == 0:
            self.timer.start(self.dt*1000) # msec
        elif count == 1:
            self.timer.pause()
        elif count ==2:
            self.timer.stop()
    
    @pyqtSlot(float)
    def setMotor(self, vel: float):
        self.joints[0].setParam(ode.ParamVel, vel)
        
    def coord(self, c):
        print(c[0], c[1])
        return c[0], c[1]
    
    def controlPID(self):
        D_state = 0
        I_state = 0
        I_state_max = 500
        I_state_min = -500
        P_const = 0.05
        D_const = 0
        I_const = 0
        # Control system (PID)
        a = (self.angle * 180 / 3.145) - self.target
        if a < -180:
            a += 360
        elif a > 180:
            a -= 360
        a_err = -a
        P_term = P_const * a_err

        D_term = D_const * ( a_err - D_state)
        D_state = a_err

        I_state = I_state + a_err
        if I_state > I_state_max: 
            I_state = I_state_max
        elif I_state < I_state_min:
            I_state = I_state_min
        I_term = I_state * I_const
        
        command_vel = P_term + I_term + D_term
        if command_vel >1:
            command_vel = 1
        elif command_vel <-1:
            command_vel = -1
        return command_vel
    
    def getrot(self):
        print(self.bodies[0].getPosition())
        print(self.bodies[0].getRotation())
    
    def drawlinks(self, vlinksitems):
        def draw(c1, c2):
            self.painter.drawLine(QPointF(c1[0], -c1[1])*self.zoom, QPointF(c2[0], -c2[1])*self.zoom)
        for name, vlink in vlinksitems:
            if name == 'ground':
                continue
            pos = [self.bodies[n].getPosition() for n in vlink]
            for n in range(0, len(pos)):
                self.painter.setPen(self.pen)
                draw(pos[n-1], pos[n])
    def drawpath(self):
        x, y, z = self.bodies[0].getPosition()
        self.path = QPainterPath((x, y))
    
    def paintEvent(self, event):
        """draw and Canvas"""
        self.painter = QPainter()
        
        self.painter.begin(self)
        self.painter.fillRect(event.rect(), QBrush(Qt.white))
        self.painter.translate(self.width()/2, self.height()/2)
        self.pen = QPen(Qt.black) 
        self.pen.setWidth(3)
        if self.vlinks != None:
            self.drawlinks(self.vlinks.items())
            self.angle = self.joints[0].getAngle()
            self.setMotor(self.controlPID())
            self.simcontrol2real.emit(str(self.controlPID()))
            self.plotdata.append(self.controlPID())
        self.painter.end()
    

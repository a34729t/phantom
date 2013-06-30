# Doesn't run under py2.7 on OSX10.6 at least on my machine

import objc, re, os
from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper
from multiprocessing import Pipe

status_images = {'idle':'./phantom.png'}

class NCruses():
    def __init__():
        return

class OSXstatusbaritem(NSObject):
    images = {}
    statusbar = None
    state = 'idle'

    @classmethod
    def start(self, pipe):
        self.pipe = pipe
        self.start_time = NSDate.date()
        app = NSApplication.sharedApplication()
        delegate = self.alloc().init()
        app.setDelegate_(delegate)
        AppHelper.runEventLoop()

    def applicationDidFinishLaunching_(self, notification):
        statusbar = NSStatusBar.systemStatusBar()
        # Create the statusbar item
        self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        # Load all images
        for i in status_images.keys():
            self.images[i] = NSImage.alloc().initByReferencingFile_(status_images[i])
        # Set initial image
        self.statusitem.setImage_(self.images['idle'])
        # self.statusitem.setAlternateImage_(self.images['highlight'])
        # Let it highlight upon clicking
        self.statusitem.setHighlightMode_(1)
        # Set a tooltip
        self.statusitem.setToolTip_('Sample app')

        # Build a very simple menu
        self.menu = NSMenu.alloc().init()
        # Start and stop service
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Start Service', 'startService:', '')
        self.menu.addItem_(menuitem)
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Stop Service', 'stopService:', '')
        self.menu.addItem_(menuitem)
        # Add a separator
        menuitem = NSMenuItem.separatorItem()
        self.menu.addItem_(menuitem)
        # Terminate event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        self.menu.addItem_(menuitem)
        # Bind it to the status item
        self.statusitem.setMenu_(self.menu)

        # Get the timer going
        self.timer = NSTimer.alloc().initWithFireDate_interval_target_selector_userInfo_repeats_(self.start_time, 5.0, self, 'tick:', None, True)
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
        self.timer.fire()

    def tick_(self, notification):
        print self.state

    def startService_(self, notification):
        self.pipe.send(["foobar", None])
        print "starting service"

    def stopService_(self, notification):
        
        print "stopping service"
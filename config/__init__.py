import ogre.renderer.OGRE as Ogre
from ogre.renderer.OGRE.sf_OIS import *
from .log import *
from PythonOgreConfig import *


Ogre.OgreVersion = Ogre.GetOgreVersion()
Ogre.OgreVersionString = Ogre.OgreVersion[0] + Ogre.OgreVersion[1] + Ogre.OgreVersion[2]
Ogre.PythonOgreVersion = Ogre.GetPythonOgreVersion()

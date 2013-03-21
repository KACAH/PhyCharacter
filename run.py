import ogre.renderer.OGRE as Ogre

from application import RagdollApplication


if __name__ == "__main__":
    try:
        _application = RagdollApplication()
        _application.go()
    except Ogre.OgreException, _e:
        print _e

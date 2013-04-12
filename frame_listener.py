import random, sys
from math import *

import ogre.renderer.OGRE as Ogre
from ogre.io import OIS
from ogre.physics import bullet
from ogre.physics import OgreBulletC, OgreBulletD

from config import FrameListener
from ragdoll.character import Character


BOX_NUM = 1000


class RagdollFrameListener(FrameListener):
    """Frame updater"""

    def __init__(self, renderWindow, camera, app):
        FrameListener.__init__(self, renderWindow, camera)

        self.app = app
        self.boxes = []
        # create test boxes if neccessary
        #self.create_boxes()
        self.character = Character(self.app)

    def create_boxes(self):
        """Create couple of boxes"""

        _scale_factor = 0.1
        for _i in xrange(BOX_NUM):
            _scale = (random.random() * 0.5 + 0.1) * _scale_factor
            _position = Ogre.Vector3((random.random() - 0.5) * 800.0,
                (random.random()) * 500.0,
                (random.random() - 0.5) * 800.0
            )
            _quat = Ogre.Quaternion(0, 0, 0, 1)
            self.boxes.append(
                self.create_box(str(_i), "Cube",
                    _position, _quat, _scale, bodyMass=100
                )
            )

    def create_box(self, id, instanceName, pos, quat, scale,
        mesh = "cube.mesh", material = "Examples/BumpyMetal",
        bodyRestitution=0.3, bodyFriction=0.3, bodyMass=10.0):
        """Create one box element"""

        _entity = self.app.sceneManager.createEntity(
            instanceName + id, mesh
        )
        _entity.setQueryFlags(1<<2)
        _entity.setCastShadows(True)
        _entity.setMaterialName(material)

        _boundingB = _entity.getBoundingBox()
        _size = _boundingB.getSize()
        _size /= 2.0 # only the half needed
        #_size *= 0.95 # Bullet margin is a bit bigger so we need a smaller size
        #_size *= scale

        _cube_shape = OgreBulletC.BoxCollisionShape(_size)
        _ph_body = OgreBulletD.RigidBody(
            instanceName + "Body" + id, self.app.world
        )

        _node = self.app.sceneManager.getRootSceneNode().createChildSceneNode()
        #_node.scale(scale, scale, scale)
        _ph_body.setShape(_node, _cube_shape,
            bodyRestitution, bodyFriction, bodyMass,
            pos, quat
        )
        _node.attachObject(_entity)
        return (_node, _entity, _cube_shape, _ph_body)

    def frameStarted(self, evt):
        self.character.update_pre_physics(evt.timeSinceLastFrame)
        self.app.world.stepSimulation(evt.timeSinceLastFrame)
        self.character.update_post_physics(evt.timeSinceLastFrame)

        return FrameListener.frameStarted(self, evt)

    def frameEnded(self, evt):
        return FrameListener.frameEnded(self, evt)

    def _processUnbufferedKeyInput(self, evt):
        if self.Keyboard.isKeyDown(OIS.KC_SPACE):
            pass

        return FrameListener._processUnbufferedKeyInput(self, evt)

import random, sys
from math import *

import ogre.renderer.OGRE as Ogre
from ogre.io import OIS
from ogre.physics import bullet
from ogre.physics import OgreBulletC, OgreBulletD

from config import FrameListener
from ragdoll.character import Character


BOX_NUM = 1000
BOX_SCALE = 0.02
BOX_MASS = 20.0

TIME_SCALE = 0.1


class RagdollFrameListener(FrameListener):
    """Frame updater"""

    id = 0

    def __init__(self, renderWindow, camera, app):
        FrameListener.__init__(self, renderWindow, camera)

        self.app = app
        self.boxes = []
        # create test boxes if neccessary
        #self.create_boxes()
        self.character = Character(self.app)
        self.shot_cooldown = 0

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
        if self.shot_cooldown > 0:
            self.shot_cooldown -= evt.timeSinceLastFrame

        _time = evt.timeSinceLastFrame * TIME_SCALE

        self.character.update_pre_physics(_time)
        self.app.world.stepSimulation(_time)
        self.character.update_post_physics(_time)

        return FrameListener.frameStarted(self, evt)

    def frameEnded(self, evt):
        return FrameListener.frameEnded(self, evt)

    def _processUnbufferedKeyInput(self, evt):
        if self.Keyboard.isKeyDown(OIS.KC_SPACE) and self.shot_cooldown <= 0:
            # starting position of the box
            _position = (self.app.camera.getDerivedPosition() \
                + self.app.camera.getDerivedDirection().normalisedCopy() * 10)
            # create an ordinary, Ogre mesh with texture
            _entity = self.app.sceneManager.createEntity(
               "Box" + str(self.id), "cube.mesh")
            _entity.setCastShadows(True)
            # we need the bounding box of the box to be able to set the size of the Bullet-box
            _boundingB = _entity.getBoundingBox()
            _size = _boundingB.getSize()
            _size /= 2.0 # only the half needed
            _size *= 0.96   # Bullet margin is a bit bigger so we need a smaller size
                              # (Bullet 2.76 Physics SDK Manual page 18)
            _entity.setMaterialName("Examples/BumpyMetal")
            _node = self.app.sceneManager.getRootSceneNode().createChildSceneNode()
            _node.attachObject(_entity)
            _node.scale(BOX_SCALE, BOX_SCALE, BOX_SCALE)
            _size *= BOX_SCALE                  # don't forget to scale down the Bullet-box too
            # after that create the Bullet shape with the calculated size
            _sceneBoxShape = OgreBulletC.BoxCollisionShape(_size)
            # and the Bullet rigid body
            _defaultBody = OgreBulletD.RigidBody(
               "defaultBoxRigid" + str(self.id), self.app.world
            )
            _defaultBody.setShape(
                _node, _sceneBoxShape,
                0.6, 0.6, BOX_MASS,
                _position, Ogre.Quaternion(0, 0, 0, 1)
            )
            _defaultBody.setLinearVelocity(
                  self.app.camera.getDerivedDirection().normalisedCopy() * 70.0
            )
            # push the created objects to the deques
            self.boxes.append((_entity, _node, _sceneBoxShape, _defaultBody))
            self.id += 1
            self.shot_cooldown = 2

        return FrameListener._processUnbufferedKeyInput(self, evt)

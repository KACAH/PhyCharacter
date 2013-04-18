import ogre.renderer.OGRE as Ogre
from ogre.physics import bullet
from ogre.physics import OgreBulletC, OgreBulletD

from config import Application
from collision_masks import *
from frame_listener import RagdollFrameListener


DEBUG = True
CAMERA_POSITION = (0, 5, -470)
GRAVITY = Ogre.Vector3(0, -9.81, 0)


class Wall(object):
    id = 0

    def __init__(self, app, pos, quat,
        mesh = "cube.mesh", material = "Examples/BumpyMetal",
        bodyRestitution=0.3, bodyFriction=0.3):

        self.app = app
        self.entity = self.app.sceneManager.createEntity(
            "Wall" + str(self.id), mesh
        )
        self.entity.setQueryFlags(1<<2)
        self.entity.setCastShadows(True)
        self.entity.setMaterialName(material)

        _boundingB = self.entity.getBoundingBox()
        _size = _boundingB.getSize()
        _size /= 2.0 # only the half needed
        #_size *= 0.95 # Bullet margin is a bit bigger so we need a smaller size

        self.cube_shape = OgreBulletC.BoxCollisionShape(_size)
        self.ph_body = OgreBulletD.RigidBody(
            "WallBody" + str(self.id), self.app.world
        )

        self.node = \
            self.app.sceneManager.getRootSceneNode().createChildSceneNode()
        self.ph_body.setShape(self.node, self.cube_shape,
            bodyRestitution, bodyFriction, 0,
            pos, quat
        )
        self.node.attachObject(self.entity)
        self.id += 1


class RagdollApplication(Application):

    def create_camera(self):
        """Create world camera"""

        self.cameraNode = \
            self.sceneManager.getRootSceneNode().createChildSceneNode()
        self.cameraNode.attachObject(self.camera)
        self.cameraNode.setPosition(CAMERA_POSITION)

    def create_sky(self):
        """create sky dome and illumination"""

        self.sceneManager.setAmbientLight((0.6, 0.6, 0.6))

        self.sceneManager.setSkyDome(True, "Examples/CloudySky", 5, 8)
        _light = self.sceneManager.createLight("MainLight")
        _light.setPosition(20, 80, 50)

    def create_physics_world(self):
        """Create bullet physics world"""

        def _fix_resource():
            """Add new resource group to fix bug with DebugDrawer"""
            _rsm = Ogre.ResourceGroupManager.getSingleton()
            _rsm.createResourceGroup("OgreBulletCollisions")

        _bounds = Ogre.AxisAlignedBox(
            (-1000, -1000, -1000), (1000,  1000,  1000)
        )
        self.world = OgreBulletD.DynamicsWorld(
            self.sceneManager, _bounds, GRAVITY
        )

        if DEBUG:
            _fix_resource()
            self.debugDrawer = OgreBulletC.DebugDrawer()
            self.debugDrawer.setDrawWireframe(True)
            self.world.setDebugDrawer(self.debugDrawer)
            self.world.setShowDebugShapes(True)
            self.debugNode = self.sceneManager.getRootSceneNode() \
                .createChildSceneNode("DebugDrawer")
            self.debugNode.attachObject(self.debugDrawer)

    def create_floor(self):
        """Create floor plane"""

        _plane = Ogre.Plane()
        _plane.normal = Ogre.Vector3().UNIT_Y
        _plane.d = 0
        Ogre.MeshManager.getSingleton().createPlane("FloorPlane",
            Ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME,
            _plane, 200000.0, 200000.0, 20, 20, True, 1, 9000, 9000,
            Ogre.Vector3().UNIT_Z
        )

        _ent = self.sceneManager.createEntity("Floor", "FloorPlane")
        _ent.setMaterialName("Examples/GrassFloor")
        self.sceneManager.getRootSceneNode()\
            .createChildSceneNode().attachObject(_ent)

        self.plane_shape = \
            OgreBulletC.StaticPlaneCollisionShape(Ogre.Vector3(0, 1, 0), 0)
        self.plane_body = OgreBulletD.RigidBody("BasePlane", self.world,
            WORLD_MASK, WORLD_COLLIDE_WITH)
        self.plane_body.setStaticShape(self.plane_shape, 0.1, 0.8)

    def create_walls(self):
        """Create testing walls"""

        #self.wall1 = Wall(
        #    self, Ogre.Vector3(53, 0, 0), Ogre.Quaternion(0, 0, 0, 1)
        #)

    def _createScene(self):
        self.create_camera()
        self.create_sky()
        self.create_physics_world()
        self.create_floor()
        self.create_walls()

    def _createFrameListener(self):
        self.frameListener = \
            RagdollFrameListener(self.renderWindow, self.camera, self)
        self.root.addFrameListener(self.frameListener)

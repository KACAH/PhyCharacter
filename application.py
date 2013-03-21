import ogre.renderer.OGRE as Ogre
from ogre.physics import bullet
from ogre.physics import OgreBulletC, OgreBulletD

from config import Application
from frame_listener import RagdollFrameListener


DEBUG = True
CAMERA_POSITION = (0, 5, -470)
GRAVITY = Ogre.Vector3(0, -9.81, 0)


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
        _ent.setMaterialName("Examples/BumpyMetal")
        self.sceneManager.getRootSceneNode()\
            .createChildSceneNode().attachObject(_ent)

        self.plane_shape = \
            OgreBulletC.StaticPlaneCollisionShape(Ogre.Vector3(0, 1, 0), 0)
        self.plane_body = OgreBulletD.RigidBody("BasePlane", self.world)
        self.plane_body.setStaticShape(self.plane_shape, 0.1, 0.8)

    def _createScene(self):
        self.create_camera()
        self.create_sky()
        self.create_physics_world()
        self.create_floor()

    def _createFrameListener(self):
        self.frameListener = \
            RagdollFrameListener(self.renderWindow, self.camera, self)
        self.root.addFrameListener(self.frameListener)

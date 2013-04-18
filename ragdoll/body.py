from math import sqrt, pi
import yaml

import ogre.renderer.OGRE as Ogre
from ogre.physics import bullet
from ogre.physics import OgreBulletC, OgreBulletD

from collision_masks import *



id = 0
buffer = []

def create_debug_point(app, pos):
    global id
    global buffer

    _en = app.sceneManager.createEntity("en" + str(id), "sphere.mesh")
    id += 1
    _node = app.sceneManager.getRootSceneNode().createChildSceneNode()
    _node.attachObject(_en)
    _node.scale(0.002, 0.002, 0.002)
    _node.setPosition(pos)
    buffer.extend((_en, _node))


class Dummy(object):
    """Empty rigid body. Used as ragdoll parts controller."""

    MASS = 1

    def __init__(self, app, pos, rot):
        self.app = app

        self.shape = bullet.btEmptyShape()
        _tr = bullet.btTransform()
        _tr.setIdentity()
        _tr.setOrigin(bullet.btVector3(pos.x, pos.y, pos.z))
        _tr.setRotation(bullet.btQuaternion(rot.x, rot.y, rot.z, rot.w))

        _local_inertia = bullet.btVector3(0,0,0)
        self.shape.calculateLocalInertia(self.MASS, _local_inertia)

        self.motion_state = bullet.btDefaultMotionState(_tr)

        self.rb_info = bullet.btRigidBody.btRigidBodyConstructionInfo(
            self.MASS, self.motion_state, self.shape, _local_inertia)
        self.body = bullet.btRigidBody(self.rb_info)
        self.body.setCollisionFlags(self.body.getCollisionFlags() \
            | bullet.btCollisionObject.CF_KINEMATIC_OBJECT)

        self.app.world.getBulletDynamicsWorld().addRigidBody(self.body)

    def setPosition(self, pos):
        _tr = bullet.btTransform()
        self.body.getMotionState().getWorldTransform(_tr)
        _tr.setOrigin(bullet.btVector3(pos.x, pos.y, pos.z))
        self.body.getMotionState().setWorldTransform(_tr)
        #self.body.setPosition(bullet.btVector3(pos.x, pos.y, pos.z))

    def setOrientation(self, rot):
        _tr = bullet.btTransform()
        self.body.getMotionState().getWorldTransform(_tr)
        _tr.setRotation(bullet.btQuaternion(rot.x, rot.y, rot.z, rot.w))
        self.body.getMotionState().setWorldTransform(_tr)
        #self.body.setOrientation(bullet.btQuaternion(rot.x, rot.y, rot.z, rot.w))


class RagdollPart(object):
    """One element of ragdoll body"""

    def __init__(self, name, app, params, node, bone_real, bone_phantom):
        self.name = name
        self.app = app
        self.parent_node = node
        self.bone = bone_real
        self.phantom = bone_phantom
        self.mass = params["mass"]
        self.width = params["width"]
        self.height = params["height"]
        self.depth = params["depth"]
        self.offset = Ogre.Vector3(0, self.height, 0) \
            + Ogre.Vector3(*params.get("offset", (0, 0, 0)))

        self.create_body()
        self.create_control_joint()

        #Temporaly and only for testing
        #if name in ("chest", ):
        #self.ph_body.setKinematicObject(True)

        self.ogre_global_bind_orientation = \
            self.phantom._getDerivedOrientation()
        self.physics_bind_orientation_inverse = \
            self.ph_body.getWorldOrientation().Inverse()

    def create_body(self):
        self.shape = OgreBulletC.BoxCollisionShape(
            Ogre.Vector3(self.width, self.height, self.depth)
        )

        self.ph_body = OgreBulletD.RigidBody(self.name, self.app.world)
        self.node = \
            self.app.sceneManager.getRootSceneNode().createChildSceneNode()

        _orient = self.bone._getDerivedOrientation()
        _pos = self.parent_node._getDerivedPosition() \
            + self.bone._getDerivedPosition() + _orient * self.offset
        self.ph_body.setShape(self.node, self.shape,
            0.3, 0.3, self.mass,
            _pos, _orient
        )

    def create_control_joint(self):
        self.dummy = Dummy(self.app, self.getPosition(), self.getOrientation())
        _pos = self.getLinkPos()

        def _create_simple_tr():
            _tr = bullet.btTransform()
            _tr.setIdentity()
            _tr.setOrigin(bullet.btVector3(0, 0, 0))
            _tr.setRotation(bullet.btQuaternion(0, 0, 0, 1))
            return _tr

        _tr1 = _create_simple_tr()
        _tr2 = _create_simple_tr()

        self.control_joint = bullet.btConeTwistConstraint(
            self.ph_body.getBulletRigidBody(), self.dummy.body, _tr1, _tr2)
        self.control_joint.setLimit(0.0, 0.0, 0.0, 0.0)
        self.switch_control_joint(True)

    def switch_control_joint(self, state):
        _world = self.app.world.getBulletDynamicsWorld()
        if state:
            _world.addConstraint(self.control_joint)
        else:
            _world.removeConstraint(self.control_joint)

    def fit_to_skeleton(self):
        _pos = self.parent_node.getOrientation() * (
            self.phantom._getDerivedPosition()
        )
        _pos = _pos + self.parent_node.getPosition()

        _rot = self.phantom._getDerivedOrientation() * \
            self.ogre_global_bind_orientation.Inverse() * \
            self.physics_bind_orientation_inverse.Inverse()

        _rot = self.parent_node.getOrientation() * _rot
        self.dummy.setPosition(_pos)
        self.dummy.setOrientation(_rot)

    def fit_to_ragdoll(self):
        _node_rotation_inverse = self.parent_node.getOrientation().Inverse()

        _physics_rotation = self.getOrientation() * \
            self.physics_bind_orientation_inverse
        _parent_inverse = \
            self.bone.getParent()._getDerivedOrientation().Inverse() * \
            _node_rotation_inverse
        _ogre_global_quat = \
            _physics_rotation * self.ogre_global_bind_orientation

        self.bone.setOrientation(_parent_inverse * _ogre_global_quat)

    def getLinkPos(self):
        return -self.offset

    def getWorldLinkPos(self):
        return self.getPosition() + self.getOrientation() * self.getLinkPos()

    def getJointPos(self, link_pos):
        _res = self.getOrientation().Inverse() * (link_pos - self.getPosition())
        return _res

    def getPosition(self):
        return self.ph_body.getWorldPosition()

    def getOrientation(self):
        return self.ph_body.getWorldOrientation()

    def getTransform(self):
        return self.ph_body.getBulletRigidBody().getWorldTransform()

    def addConstraintRef(self, constraint):
        self.ph_body.getBulletRigidBody().addConstraintRef(
            constraint.getBulletTypedConstraint()
        )


class Ragdoll(object):
    """Character ragdoll body"""

    def __init__(self, app, ragdoll_file, entity, phantom, node):
        self.app = app
        self.entity = entity
        self.phantom = phantom
        self.node = node

        self.bone_binds = {}
        self.parts = {}
        self.joints = {}

        self.reset_bones()

        _config = yaml.load(file(ragdoll_file))
        self.root_part = _config["root_part"]
        self.root_offset = Ogre.Vector3(*_config["root_offset"])

        self.load_parts(_config["parts"])
        self.load_joints(_config["joints"])

    def reset_bones(self):
        _bone_iter = self.entity.getSkeleton().getBoneIterator()
        while _bone_iter.hasMoreElements():
            _bone = _bone_iter.getNext()
            _bone.setManuallyControlled(True)
            _bone.reset()

    def load_parts(self, p_config):
        for _part_name, _part_data in p_config.items():
            _part = RagdollPart(
                _part_name, self.app, _part_data, self.node,
                self.entity.getSkeleton().getBone(_part_data["bone"]),
                self.phantom.getSkeleton().getBone(_part_data["bone"]),
            )
            self.parts[_part_name] = _part
            self.bone_binds[_part_data["bone"]] = _part

    def create_cone_twist(self, config):
        _partA = self.parts[config["partA"]]
        _partB = self.parts[config["partB"]]

        _joint_pos = _partA.getJointPos(_partB.getWorldLinkPos())
        _rot = (_partA.getOrientation().Inverse() * _partB.getOrientation()) \
            * Ogre.Quaternion(0, 0, 0, 1)

        _joint = OgreBulletD.ConeTwistConstraint(
            _partA.ph_body,
            _partB.ph_body,
            _joint_pos, _rot,
            _partB.getLinkPos(), Ogre.Quaternion(0, 0, 0, 1),
        )
        _partA.addConstraintRef(_joint)
        _partB.addConstraintRef(_joint)

        _btJoint = _joint.getBulletTypedConstraint()
        #_btJoint.setLimit(
        #    _btJoint.getSwingSpan1(),
        #    _btJoint.getSwingSpan2(),
        #    _btJoint.getTwistSpan(),
        #    0.01, 0.01, 0.01
        #)
        return _joint

    def create_fixed_joint(self, config):
        _joint = self.create_cone_twist(config)
        #_joint.getBulletTypedConstraint().setLimit(0.0, 0.0, 0.0)
        return _joint

    def create_rotating_joint(self, config):
        _joint = self.create_cone_twist(config)
        #_joint.getBulletTypedConstraint().setLimit(0.5, 0.5, 0.5)
        #_joint.getBulletTypedConstraint().setLimit(0.0, 0.0, 0.0)
        return _joint

    def load_joints(self, j_config):
        for _joint_name, _joint_data in j_config.items():
            _type = _joint_data["type"]
            if _type == "fixed":
                _joint = self.create_fixed_joint(_joint_data)
            elif _type == "rotating":
                _joint = self.create_rotating_joint(_joint_data)
            self.app.world.addConstraint(_joint)
            self.joints[_joint_name] = _joint

    def update_pre_physics(self):
        for _part in self.bone_binds.values():
            _part.fit_to_skeleton()

        _bone_iter = self.entity.getSkeleton().getBoneIterator()
        while _bone_iter.hasMoreElements():
            _bone = _bone_iter.getNext()

            if _bone.getName() not in self.bone_binds:
                _source_bone = \
                    self.phantom.getSkeleton().getBone(_bone.getName())
                _bone.setPosition(_source_bone.getPosition())
                _bone.setOrientation(_source_bone.getOrientation())

    def update_post_physics(self):
        for _part in self.bone_binds.values():
            _part.fit_to_ragdoll()

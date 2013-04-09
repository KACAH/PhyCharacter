from math import sqrt, pi
import yaml

import ogre.renderer.OGRE as Ogre
from ogre.physics import bullet
from ogre.physics import OgreBulletC, OgreBulletD

from collision_masks import *


class RagdollPart(object):
    """One element of ragdoll body"""

    def __init__(self, name, app, params, bone, pos):
        self.name = name
        self.app = app
        self.bone = bone
        self.width = params["width"]
        self.height = params["height"]
        self.depth = params["depth"]

        self.shape = OgreBulletC.BoxCollisionShape(
            Ogre.Vector3(self.width, self.height, self.depth)
        )
        self.ph_body = OgreBulletD.RigidBody(
            params["bone"], self.app.world, RAGDOLL_MASK, RAGDOLL_COLLIDE_WITH
        )
        self.node = \
            self.app.sceneManager.getRootSceneNode().createChildSceneNode()

        self.offset = Ogre.Vector3(*params.get("offset", [0, 0, 0]))
        _pos = pos + bone._getDerivedPosition()
        _orient = bone._getDerivedOrientation()
        self.ph_body.setShape(self.node, self.shape,
            0.3, 0.3, params["mass"],
            _pos, _orient
        )
        self.ph_body.setKinematicObject(True)

        self.ogre_global_bind_orientation = bone._getDerivedOrientation()
        self.physics_bind_orientation_inverse = \
            self.ph_body.getWorldOrientation().Inverse();


class Ragdoll(object):
    """Character ragdoll body"""

    def __init__(self, app, ragdoll_file, entity, anim_state, node):
        self.app = app
        self.entity = entity
        self.anim_state = anim_state
        self.anim_state.createBlendMask(self.entity.getSkeleton().getNumBones())
        self.node = node

        self.bone_binds = {}
        self.parts = {}
        self.joints = {}

        _config = yaml.load(file(ragdoll_file))
        self.root_part = _config["root_part"]
        self.root_offset = Ogre.Vector3(*_config["root_offset"])

        self.load_parts(_config["parts"])
        self.load_joints(_config["joints"])

    def load_parts(self, p_config):
        for _part_name, _part_data in p_config.items():
            _part = RagdollPart(
                _part_name, self.app, _part_data,
                self.entity.getSkeleton().getBone(_part_data["bone"]),
                self.node._getDerivedPosition()
            )
            self.parts[_part_name] = _part
            self.bone_binds[_part_data["bone"]] = _part

    def create_cone_twist(self, config):
        _partA = self.parts[config["partA"]]
        _partB = self.parts[config["partB"]]
        _joint = OgreBulletD.ConeTwistConstraint(
            _partA.ph_body,
            _partB.ph_body,
            Ogre.Vector3(*config["pointA"]),
            _partA.bone._getDerivedOrientation(),
            Ogre.Vector3(*config["pointB"]),
            _partB.bone._getDerivedOrientation(),
        )
        return _joint

    def create_fixed_joint(self, config):
        _joint = self.create_cone_twist(config)
        _joint.setLimit(0.04, 0.04, 0.04)
        return _joint

    def create_rotating_joint(self, config):
        _joint = self.create_cone_twist(config)
        _joint.setLimit(0.5, 0.5, 0.5)
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

    def get_fit_to_skeleton(self, part):
        _pos = self.node.getOrientation() * (
            part.bone._getDerivedPosition()
        )
        _pos = _pos + self.node.getPosition()

        _rot = part.bone._getDerivedOrientation() * \
            part.ogre_global_bind_orientation.Inverse() * \
            part.physics_bind_orientation_inverse.Inverse()

        #part.ph_body.setPosition(_pos)
        #part.ph_body.setOrientation(self.node.getOrientation() * _rot)
        return (_pos, self.node.getOrientation() * _rot)

    def fit_to_ragdoll(self, part):
        _node_rotation_inverse = self.node.getOrientation().Inverse()

        _physics_rotation = part.ph_body.getWorldOrientation() * \
            part.physics_bind_orientation_inverse
        _parent_inverse = \
            part.bone.getParent()._getDerivedOrientation().Inverse() * \
            _node_rotation_inverse
        _ogre_global_quat = \
            _physics_rotation * part.ogre_global_bind_orientation

        part.bone.setOrientation(_parent_inverse * _ogre_global_quat)

        #for _part in self.parts.values():
        #    _part.bone._setDerivedOrientation(
        #        _part.ph_body.getWorldOrientation()
        #    )

    def update_animation(self):
        _bone_iter = self.entity_phantom.getSkeleton().getBoneIterator()

        while _bone_iter.hasMoreElements():
            _source_bone = _bone_iter.getNext()
            _name = _source_bone.getName()
            _target_bone = self.entity.getSkeleton().getBone(_name)

            if _name in self.bone_binds:
                _cur_pos = _target_bone._getDerivedPosition()
                _target_pos = _source_bone._getDerivedPosition()

                self.bone_binds[_name].ph_body.applyImpulse(
                    (_target_pos - _cur_pos) * 10, Ogre.Vector3(0, 0, 0)
                )
            else:
                _target_bone.setOrientation(_source_bone.getOrientation())

    def set_skeleton_mode(self, active):
        self.skeleton_mode = active

        for (_part_name, _part) in self.parts.items():
            _part.ph_body.setKinematicObject(active)
            #if _part_name == "waist":
            #    _part.ph_body.setKinematicObject(True)
            #else:
            #    _part.ph_body.setKinematicObject(False)

        _bone_iter = self.entity.getSkeleton().getBoneIterator()
        while _bone_iter.hasMoreElements():
            _bone = _bone_iter.getNext()
            _bone.setManuallyControlled(not active)
            _bone.reset()

    def fit_animated_bone(self, bone):
        bone.setManuallyControlled(True)
        bone.reset()
        self.anim_state.setBlendMaskEntry(bone.getHandle(), 1)

    def fit_ragdolled_bone(self, bone):
        _part = self.bone_binds[bone.getName()]

        EQUAL_DELTA = 0

        (_skel_pos, _skel_rot) = self.get_fit_to_skeleton(_part)
        (_cur_pos, _cur_rot) = \
            _part.ph_body.getWorldPosition(), _part.ph_body.getWorldOrientation()

        _pos_diff = _skel_pos - _cur_pos
        if False:#_pos_diff.length() > EQUAL_DELTA:
            bone.setManuallyControlled(False)
            bone.reset()
            self.anim_state.setBlendMaskEntry(bone.getHandle(), 1)

            _part.ph_body.setKinematicObject(True)
            _part.ph_body.setPosition(_skel_pos)
            _part.ph_body.setOrientation(_skel_rot)
        else:

            bone.setManuallyControlled(True)
            bone.reset()
            self.anim_state.setBlendMaskEntry(bone.getHandle(), 0)

            if _part.name == "thigh_r":
                _part.ph_body.setKinematicObject(True)
            else:
                _part.ph_body.setKinematicObject(False)
            #_part.ph_body.applyForce(_pos_diff, Ogre.Vector3(0, 0, 0))
            self.fit_to_ragdoll(_part)

    def update(self, time):
        _bone_iter = self.entity.getSkeleton().getBoneIterator()
        while _bone_iter.hasMoreElements():
            _bone = _bone_iter.getNext()

            if _bone.getName() in self.bone_binds:
                self.fit_ragdolled_bone(_bone)
            else:
                self.fit_animated_bone(_bone)

        self.node.setPosition(
            self.parts[self.root_part].ph_body.getWorldPosition() + \
                self.root_offset
        )

import ogre.renderer.OGRE as Ogre

from body import Ragdoll


MESH = "Sinbad.mesh"
RAGDOLL_FILE = "ragdoll.yaml"
ANIMATION = "RunBase"
POSITION = (0, 5, 0)


class Character(object):
    """Animated character with ragdoll system"""

    def __init__(self, app):
        self.app = app
        self.create_mesh()

    def create_phantom(self):
        self.phantom_ent = self.app.sceneManager.createEntity("Phantom", MESH)

        for _ii in xrange(self.phantom_ent.getNumSubEntities()):
            _sub_entity = self.phantom_ent.getSubEntity(_ii)
            _sub_entity.setMaterialName(
                #_sub_entity.getMaterialName() + "Transparent"
                "Sinbad/GreyTransparent"
            )

        self.phantom_node = self.node.createChildSceneNode()
        self.phantom_node.attachObject(self.phantom_ent)
        self.phantom_node.scale(0.01, 0.01, 0.01)

    def create_mesh(self):
        """Create visual mesh"""

        self.node = \
            self.app.sceneManager.getRootSceneNode().createChildSceneNode()
        self.node.setPosition(POSITION)

        self.entity = self.app.sceneManager.createEntity("Character", MESH)
        self.node.attachObject(self.entity)

        self.create_phantom()

        self.anim_state = self.phantom_ent.getAnimationState(ANIMATION)
        self.anim_state.setEnabled(True)
        self.anim_state.setLoop(True)

        self.ragdoll = Ragdoll(self.app, RAGDOLL_FILE, \
            self.entity, self.phantom_ent, self.node)

    def update_pre_physics(self, time):
        self.anim_state.addTime(time)
        self.ragdoll.update_pre_physics()

    def update_post_physics(self, time):
        self.ragdoll.update_post_physics()

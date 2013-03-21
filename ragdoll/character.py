import ogre.renderer.OGRE as Ogre


MESH = "Sinbad.mesh"
ANIMATION = "Dance"
POSITION = (0, 5, 0)


class Character(object):
    """Animated character with ragdoll system"""

    def __init__(self, app):
        self.app = app
        self.create_mesh()

    def create_mesh(self):
        """Create visual mesh"""

        self.entity = self.app.sceneManager.createEntity("Character", MESH)
        self.node = self.app.sceneManager.getRootSceneNode().createChildSceneNode()
        self.node.attachObject(self.entity)
        self.node.setPosition(POSITION)
        self.anim_state = self.entity.getAnimationState(ANIMATION)
        self.anim_state.setEnabled(True)
        self.anim_state.setLoop(True)

    def update(self, time):
        """Update character state"""
        self.anim_state.addTime(time)

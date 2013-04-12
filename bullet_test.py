import ogre.renderer.OGRE as Ogre
from ogre.physics import bullet
from ogre.physics import OgreBulletC, OgreBulletD


print "bullet: \n", dir(bullet), "\n"
print "BulletC: \n", dir(OgreBulletC), "\n"
print "BulletD: \n", dir(OgreBulletD), "\n"

print "\n\n"

print dir(OgreBulletD.ConeTwistConstraint)

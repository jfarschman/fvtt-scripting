// Khul Shield - a large protective shield around the BBEG

new Sequence()

// Persist the ring
.effect()
.fadeIn(5000)
.atLocation(token)
.spriteOffset({ x: 65, y: 90 })
//.file("jb2a.shield.01.loop.blue")
.file("jb2a.markers.smoke.ring.loop.bluepurple")
.atLocation(token)
.scale(1.5)
.persist()

.play()

// Make a magical field around a thing

new Sequence()

// Persist the ring
.effect()
.fadeIn(5000)
.atLocation(token)
.spriteOffset({ x: 0, y: 0 })
//.file("jb2a.static_electricity.01.blue")
.file("jb2a.magic_signs.circle.02.evocation.complete")
//.file("jb2a.magic_signs.circle.01")
.atLocation(token)
.scale(0.5)
.persist()

.play()

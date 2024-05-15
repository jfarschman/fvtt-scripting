// Khul Powers - strands of energy flow into the BBEG
// From a source, target him and invoke this.

const target = game.user.targets.first();

new Sequence()
    .effect()
        .file("jb2a.energy_strands.range.multiple.bluepink.02")
        .attachTo(token)
        .stretchTo(target, { attachTo: true })
        .persist()
    .play()

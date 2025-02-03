//macro for dnd5e - updated for v4.2.2 and v12 of FoundryVTT
// requires: Sequencer

const members = game.actors.getName("Party").system.members; //name of the group actor where the party is added to here.
for (const {actor} of members) {
  const location = await Sequencer.Crosshair.show({
    icon: {
      texture: actor.prototypeToken.texture.src,
      borderVisible: false
    },
    label: {
      text: actor.name
    }
  });
  if (!location) continue; // skip over a token by right clicking
  const { x, y } = canvas.tokens.getSnappedPoint(location);
  const oldToken = actor.getActiveTokens(false, true)[0];
  if(oldToken) await oldToken.delete();
  const newToken = await actor.getTokenDocument({ x, y });
  await TokenDocument.create(newToken.toObject(), { parent: canvas.scene });
}

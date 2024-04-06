// - Apply Rage and insrease strength and movement. 

//Is a token selected? If not, error
console.log("Tokens: ", canvas.tokens.controlled)
if(canvas.tokens.controlled.length == 0 || canvas.tokens.controlled.length > 1){
	ui.notifications.error("Please select a single token");
	return;
}
let actor = canvas.tokens.controlled[0].actor

await Dialog.prompt({
    title: 'Brys Rage Level',
    content: `
        <div class="form-group">
          <label for="rageSelect">Select the Rage Level</label>
          <select name="rageSelect">
            <option value="raging">1 Raging</option>
            <option value="seething">2 Seething</option>
            <option value="frenzied">3 Frenzied</option>
            <option value="insane">4 Insane</option>
            <option value="reset">Reset</option>
          </select>
        </div>
    `,
        callback: async(html) => {
          let select = html.find('[name="rageSelect"]').val();
          console.log(select)

          // Handle the levels and message
          if (select === "raging") {
          	ChatMessage.create({ content: "Bry grows enraged, a dark energy invigorating her armored form.", speaker: { alias: "Bry Rage Status" } });
          	// Rage On, STR = 18, WIS = 8, MV = 40
          	//dnd5e.documents.macro.rollItem("Rage 10.0.15")
          	token.actor.update({"data.abilities.str.value": 18});
          	token.actor.update({"data.abilities.wis.value": 8});
          	token.actor.update({"system.attributes.movement.walk": 40});
          } else if (select === "seething") {
          	ChatMessage.create({ content: "Seething - Stronger, and faster, she attacks with advantage and crits on a 19-20", speaker: { alias: "Bry Rage Status" } });
          	// Rage On, STR = 20, WIS = 5, MV = 50
          	token.actor.update({"data.abilities.str.value": 20});
          	token.actor.update({"data.abilities.wis.value": 5});
          	token.actor.update({"system.attributes.movement.walk": 50});
          } else if (select === "frenzied") {
          	ChatMessage.create({ content: "Frenzied - Super natural speed and strength infuse here actions. She has an additional attack, attacks with advantage and crits on a 16-20", speaker: { alias: "Bry Rage Status" } });
          	// Rage On, STR = 22, WIS = 3, MV = 65
          	token.actor.update({"data.abilities.str.value": 22});
          	token.actor.update({"data.abilities.wis.value": 3});
          	token.actor.update({"system.attributes.movement.walk": 65});
          } else if (select === "insane") {
          	ChatMessage.create({ content: "Insane - Energy wreaths her limbs as she attacks 3 times per round with advantage, critting on every hit", speaker: { alias: "Bry Rage Status" } });
          	// Rage On, STR = 25, WIS = 1, MV = 90
          	token.actor.update({"data.abilities.str.value": 25});
          	token.actor.update({"data.abilities.wis.value": 1});
          	token.actor.update({"system.attributes.movement.walk": 90});
          } else if (select === "reset") {
          	ChatMessage.create({ content: "Noticeably shaken and depleted, Bry returns to normal.", speaker: { alias: "Bry Rage Status" } });
          	// Rage Off, STR = 25, WIS = 1, MV = 90
          	for (const tkn of canvas.tokens.controlled) {
          		const removeList = tkn.actor.temporaryEffects.map(e => e.id);
          		await tkn.actor.deleteEmbeddedDocuments("ActiveEffect", removeList)
          	}
          	token.actor.update({"data.abilities.str.value": 15});
          	token.actor.update({"data.abilities.wis.value": 16});
          	token.actor.update({"system.attributes.movement.walk": 30});
          }
    }
})

// Macro Name: Wisdom Saving Throw
// Macro Type: Script

// Step 1: Check if an actor is selected
const selectedActors = canvas.tokens.controlled;
if (selectedActors.length === 0) {
  ui.notifications.error("Please select at least one actor.");
} else {
  // Step 2: Prompt for difficulty level
  new Dialog({
    title: "Set Difficulty Level",
    content: `
      <p>Enter the difficulty level (12-25) for the corruption check:</p>
      <input type="number" id="difficulty" min="10" max="25">
    `,
    buttons: {
      ok: {
        label: "Roll",
        callback: async (html) => {
          const difficulty = parseInt(html.find("#difficulty")[0].value);
          if (isNaN(difficulty) || difficulty < 1 || difficulty > 25) {
            ui.notifications.error("Invalid difficulty level. Please enter a number between 1 and 25.");
          } else {
            // Step 3: Wisdom saving throw using MIDI-QOL
            const actor = selectedActors[0].actor;
            const midiQOLRoll = await actor.rollAbilitySave("wis", { event: event });
            //Dnd5.rollAbilitySave(actor, "wis", options)
            const success = midiQOLRoll.total >= difficulty;

            // Step 4: Report results
            let message = `Wisdom Saving Throw: ${midiQOLRoll.total}`;
            if (!success) {
              message += "\nYou have gained a corruption point!";
            }
            ChatMessage.create({
              content: message,
              speaker: ChatMessage.getSpeaker({ actor }),
            });
          }
        },
      },
      cancel: {
        label: "Cancel",
      },
    },
  }).render(true);
}

// Pick a victim from the list of users, then output the results to chat and to the console log. 
// Note: The GM is a possible victim! source - https://foundryvtt.com/article/macros/

const victims = game.users.contents;

const roll = await new Roll(`1d${victims.length} - 1`).roll();
const victim = victims[roll.total];
console.log(victim);

const victimName = scope.manualVictim ? scope.manualVictim : victim.name;

const results_html = `<h3>Victim Selected!</h3>
<p>Something bad is going to happen to <br><strong>${victimName}</strong>. Buckle up!</p>`

ChatMessage.create({
    user: game.user._id,
    content: results_html
});

return victim;

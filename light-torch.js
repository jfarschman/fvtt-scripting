main()

async function main(){
	//Is a token selected? If not, error
	if(canvas.tokens.controlled.length == 0 || canvas.tokens.controlled.length > 1){
		ui.notifications.error("Please select a single token.");
		return;
	}
	let myTokenActor = canvas.tokens.controlled[0].actor;
	let myTokenCanvas = canvas.tokens.controlled[0];
	
	// is the token already carrying a torch?
	if(myTokenCanvas.document.light.dim > 0 || myTokenCanvas.document.light.bright > 0) {
		ui.notifications.warn("You turn of the torch and throw it away.");
		// update light source
		myTokenCanvas.document.update({ light:{ bright : 0, dim: 0, color : '#663c00'}} );
		return;
	}

	//Does the token have a torch? Otherwise error
	let torch = myTokenActor.items.find(item => item.name == "Torch")
	if(torch == null || torch == undefined){
		ui.notifications.error("You don't have any torches!");
		return;
	}
	
	// user notification
	ui.notifications.warn("You pull a torch from your pack and light it.");
	
	//Subtract a torch
	await torch.update({"system.quantity": torch.system.quantity - 1})
	if(torch.system.quantity < 1){
		torch.delete();
	}
	
	// update light source
	myTokenCanvas.document.update({ light:{ bright : 5, dim: 30, color : '#663c00'}} )
}

/**
 * Daggerheart Icon Harvester
 * Scans all Actors in your World and Compendiums to build a map of Feature Names -> Icons.
 */
async function harvestIcons() {
    const iconMap = {};
    let count = 0;

    // Helper to process an actor's items
    const processItems = (items) => {
        for (const item of items) {
            // We only care about Features or similar items
            if (item.type !== "feature" && item.type !== "weapon") continue;
            
            // Normalize name: "Relentless (3)" -> "relentless"
            // This regex removes text in parentheses and trims whitespace
            const cleanName = item.name.replace(/\s*\([^)]*\)/g, "").trim().toLowerCase();
            
            // Only save if it has a custom icon (ignore default item-bag)
            if (item.img && !item.img.includes("item-bag.svg") && !item.img.includes("mystery-man")) {
                // If we haven't seen this yet, or if this version is an SVG (likely system default), 
                // we might want to prefer WebP? Actually, just first come first served is usually fine.
                if (!iconMap[cleanName]) {
                    iconMap[cleanName] = item.img;
                    count++;
                }
            }
        }
    };

    // 1. Scan World Actors (Adversaries you've already made/imported)
    console.log("Scanning World Actors...");
    for (const actor of game.actors) {
        processItems(actor.items);
    }

    // 2. Scan Compendiums (The "Modules" you mentioned)
    // We look for packs that contain Actors or Items
    console.log("Scanning Compendiums...");
    for (const pack of game.packs) {
        // Skip system default packs if you only want your module's art
        // if (pack.metadata.packageType === "system") continue; 

        const content = await pack.getDocuments();
        for (const doc of content) {
            if (doc.documentName === "Item") {
                processItems([doc]);
            } else if (doc.documentName === "Actor") {
                processItems(doc.items);
            }
        }
    }

    // 3. Export
    console.log(`Harvested ${count} unique icons.`);
    saveDataToFile(JSON.stringify(iconMap, null, 2), "text/json", "daggerheart_icon_map.json");
}

harvestIcons();

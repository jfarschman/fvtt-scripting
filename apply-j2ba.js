// Apply an J2BA on tokens 

await Dialog.prompt({
    title: 'Apply an Aura to Token(s)',
    content: `
        <div class="form-group">
            <label for="effectSelect">Select the Aura</label>
            <select name="effectSelect" id="effectSelect">
                <option value="jb2a.hunters_mark.pulse">1 Hunters Mark</option>
                <option value="jb2a.arms_of_hadar.dark_purple">2 Tentacles</option>
                <option value="jb2a.bardic_inspiration.greenorange">3 Inspiration</option>
                <option value="jb2a.magic_signs.circle.02">4 Magic Cage</option>
                <option value="jb2a.template_circle.aura">5 Creepy Aura</option>
            </select>
        </div>
    `,
    callback: async (html) => {
        const selectedEffect = html.find('[name="effectSelect"]').val();
        console.log(selectedEffect);

        // Your sequence code here

        new Sequence()
          .effect()
          .fadeIn(5000)
          .atLocation(token) 
          .spriteOffset({ x: 0, y: 0 })
          .opacity(0.5)
          .file(selectedEffect)
          .atLocation(token)
          .scale(0.5)
          .persist()
         .play()
    }
});

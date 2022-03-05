document.addEventListener("DOMContentLoaded", function () {
    const firstnameField = document.getElementById("id_first_name");
    const lastnameField = document.getElementById("id_last_name");
    const usernameField = document.getElementById("id_username");

    firstnameField.addEventListener("change", updateUsername);
    firstnameField.addEventListener("input", updateUsername);
    lastnameField.addEventListener("change", updateUsername);
    lastnameField.addEventListener("input", updateUsername);

    const character_replace_map = {
        'a': /[àáâãåăą]/g,
        'A': /[ÀÁÂÃÅĂĄ]/g,
        'c': /[ćčç]/g,
        'C': /[ĆČÇ]/g,
        'd': /[ďđ]/g,
        'D': /[ĎÐ]/g,
        'e': /[èéêëěę]/g,
        'E': /[ÈÉÊËĚĘ]/g,
        'g': /[ğ]/g,
        'G': /[Ğ]/g,
        'i': /[ìíîï]/g,
        'I': /[ÌÍÎÏ]/g,
        'l': /[ĺľł]/g,
        'L': /[ĹĽŁ]/g,
        'n': /[ñňń]/g,
        'N': /[ÑŇŃ]/g,
        'o': /[òóôõøő]/g,
        'O': /[ÒÓÔÕØ]/g,
        'r': /[řŕ]/g,
        'R': /[ŘŔ]/g,
        's': /[šş]/g,
        'S': /[ŠŞŚ]/g,
        't': /[ťţ]/g,
        'T': /[ŤŢ]/g,
        'ue': /[ü]/g,
        'UE': /[Ü]/g,
        'u': /[ùúûůµ]/g,
        'U': /[ÙÚÛŮ]/g,
        'y': /[ÿý]/g,
        'Y': /[ŸÝ]/g,
        'z': /[žźż]/g,
        'Z': /[ŽŹŻ]/g,
        'th': /[þ]/g,
        'TH': /[Þ]/g,
        'dh': /[ð]/g,
        'DH': /[Ð]/g,
        'ss': /[ß]/g,
        'oe': /[œö]/g,
        'OE': /[ŒÖ]/g,
        'ae': /[æä]/g,
        'AE': /[ÆÄ]/g
    };

    function updateUsername() {
        let firstName = firstnameField.value
        let lastName = lastnameField.value

        // str.strip()
        firstName = firstName.replace(/^\s+|\s+$/g, '');
        lastName = lastName.replace(/^\s+|\s+$/g, '');

        firstName = firstName.split(" ")[0]
        lastName = lastName.replace(" ", "-")
        let username = firstName + "." + lastName
        for (const key in character_replace_map) {
            username = username.replace(character_replace_map[key], key)
        }

        usernameField.value = username.toLowerCase();
    }

    if (usernameField.value === "") {
        updateUsername();
    }

});





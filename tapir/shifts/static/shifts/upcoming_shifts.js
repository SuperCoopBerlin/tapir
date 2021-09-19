var slot_status_filter = "no-filter";
var slot_name_filter = "any";

console.log("YO");
window.addEventListener('load', function () {
    for (let slot_status_button of document.getElementsByName("slot_status_options")) {
        slot_status_button.addEventListener("click", () => {
            slot_status_filter = slot_status_button.value;
            update_filters();
        });
    }

    for (let slot_name_button of document.getElementsByName("slot_name_options")) {
        slot_name_button.addEventListener("click", () => {
            slot_name_filter = slot_name_button.value;
            update_filters();
        });
    }

    update_filters()
});

const hidden_class = "btn-light";
const nofilter_class = "btn-outline-dark";
const selected_class = "btn-primary";
const highlight_class = "animated-shift-block";

function update_filters() {
    for (let shift_block of document.querySelectorAll(".shift-block")) {
        shift_block.classList.remove(hidden_class);
        shift_block.classList.remove(nofilter_class);
        shift_block.classList.remove(selected_class);
        shift_block.classList.remove(highlight_class);

        if (slot_status_filter == "no-filter") {
            shift_block.classList.add(nofilter_class);
            continue;
        }

        const required_class = slot_status_filter + "_" + slot_name_filter
        if (shift_block.classList.contains(required_class)) {
            shift_block.classList.add(selected_class);
        } else {
            shift_block.classList.add(hidden_class);
        }

        if (slot_status_filter == "freeslot" && shift_block.classList.contains("standin_" + slot_name_filter)) {
            shift_block.classList.add(highlight_class);
        }
    }
}
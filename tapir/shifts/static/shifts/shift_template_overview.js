var slot_name_filter = "no-filter";

window.addEventListener('load', function () {
    for (let slot_name_button of document.getElementsByName("slot_name_options")) {
        slot_name_button.addEventListener("click", () => {
            slot_name_filter = slot_name_button.value;
            update_filters();
        });
        if (slot_name_button.classList.contains("active-on-load")) {
            slot_name_button.click()
        }
    }

    document.getElementById("legend-primary").classList.add(highlight_class);
    document.getElementById("legend-secondary").classList.add(highlight_class);
    document.getElementById("legend-secondary").classList.add(secondary_highlight_class);
    document.getElementById("legend-off").classList.add(hidden_class);

    update_filters()
});

const hidden_class = "btn-light";
const nofilter_class = "btn-outline-dark";
const highlight_class = "btn-info";
const secondary_highlight_class = "fade-out";
const animate_class = "animated-shift-block";

function update_filters() {
    for (let shift_block of document.querySelectorAll(".shift-block")) {
        shift_block.classList.remove(hidden_class);
        shift_block.classList.remove(nofilter_class);
        shift_block.classList.remove(secondary_highlight_class);
        shift_block.classList.remove(highlight_class);
        shift_block.classList.remove(animate_class);

        if (slot_name_filter == "no-filter") {
            shift_block.classList.add(nofilter_class);
            continue;
        }

        const filtered_class = "freeslot_" + slot_name_filter;
        const highlighted_class = "freeslot_required_" + slot_name_filter;
        if (shift_block.classList.contains(filtered_class)) {
            shift_block.classList.add(highlight_class);
            if (!shift_block.classList.contains(highlighted_class)) {
                shift_block.classList.add(secondary_highlight_class);
            }
        } else {
            shift_block.classList.add(hidden_class);
        }
    }
}
var StatusFilter;
(function (StatusFilter) {
    StatusFilter["FREESLOT"] = "free-slot";
    StatusFilter["NO_FILTER"] = "no-filter";
    StatusFilter["NEEDS_HELP"] = "needs-help";
})(StatusFilter || (StatusFilter = {}));
class ShiftFiltersManager {
    constructor() {
        this.HIDDEN_CLASS = "btn-light";
        this.NO_FILTER_CLASS = "btn-outline-dark";
        this.HIGHLIGHT_CLASS = "btn-info";
        this.CANCELLED_CLASS = "btn-secondary";
        window.addEventListener('load', () => {
            this.init();
        });
    }
    init() {
        this.legend_highlighted = document.getElementById("legend-highlighted");
        this.legend_highlighted.classList.add(this.HIGHLIGHT_CLASS);
        let legend_hidden = document.getElementById("legend-hidden");
        legend_hidden.classList.add(this.HIDDEN_CLASS);
        let legend_cancelled = document.getElementById("legend-cancelled");
        legend_cancelled.classList.add(this.CANCELLED_CLASS);
        this.filter_legend = document.getElementById("filter-legend");
        this.slot_name_group = document.getElementById("slot-name-group");
        this.shift_blocks = Array.from(document.getElementsByClassName("shift-block"));
        for (let slot_status_button of document.getElementsByName("slot_status_options")) {
            if (slot_status_button.classList.contains("active-on-load")) {
                this.current_status_filter = slot_status_button;
                slot_status_button.click();
            }
            slot_status_button.addEventListener("click", () => {
                this.current_status_filter = slot_status_button;
                this.on_filter_changed();
            });
        }
        for (let slot_name_button of document.getElementsByName("slot_name_options")) {
            if (slot_name_button.classList.contains("active-on-load")) {
                this.current_slot_filter = slot_name_button;
                slot_name_button.click();
            }
            slot_name_button.addEventListener("click", () => {
                this.current_slot_filter = slot_name_button;
                this.on_filter_changed();
            });
        }
        this.on_filter_changed();
    }
    on_filter_changed() {
        for (let shift_block of this.shift_blocks) {
            this.update_shift_block(shift_block, this.current_status_filter.value, this.current_slot_filter.value);
        }
        this.legend_highlighted.innerText = this.current_status_filter.nextElementSibling.innerHTML;
        if (this.current_status_filter.value == StatusFilter.FREESLOT) {
            this.legend_highlighted.innerText += " - " + this.current_slot_filter.nextElementSibling.innerHTML;
        }
        this.slot_name_group.style.display = this.current_status_filter.value == StatusFilter.FREESLOT ? null : "none";
    }
    update_shift_block(shift_block, slot_status_filter, slot_name_filter) {
        if (shift_block.classList.contains("cancelled")) {
            shift_block.classList.add(this.CANCELLED_CLASS);
            return;
        }
        else {
            shift_block.classList.remove(this.CANCELLED_CLASS);
        }
        shift_block.classList.remove(this.HIDDEN_CLASS);
        shift_block.classList.remove(this.NO_FILTER_CLASS);
        shift_block.classList.remove(this.HIGHLIGHT_CLASS);
        if (shift_block.classList.contains("is_in_the_past")) {
            shift_block.classList.add(this.HIDDEN_CLASS);
            return;
        }
        let addedClass;
        switch (slot_status_filter) {
            case StatusFilter.NO_FILTER:
                addedClass = this.NO_FILTER_CLASS;
                break;
            case StatusFilter.NEEDS_HELP:
                addedClass = shift_block.classList.contains("needs_help") ? this.HIGHLIGHT_CLASS : this.HIDDEN_CLASS;
                break;
            case StatusFilter.FREESLOT:
                const filtered_class = "freeslot_" + slot_name_filter;
                addedClass = shift_block.classList.contains(filtered_class) ? this.HIGHLIGHT_CLASS : this.HIDDEN_CLASS;
                break;
        }
        shift_block.classList.add(addedClass);
    }
}
var shiftFilterManager = new ShiftFiltersManager();
//# sourceMappingURL=ShiftFiltersManager.js.map
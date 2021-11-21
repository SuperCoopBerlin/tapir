enum StatusFilter {
    FREESLOT = "free-slot",
    NO_FILTER = "no-filter",
    NEEDS_HELP = "needs-help",
}

class ShiftFiltersManager {
    readonly HIDDEN_CLASS = "btn-light";
    readonly NO_FILTER_CLASS = "btn-outline-dark";
    readonly HIGHLIGHT_CLASS = "btn-info";

    private legend_highlighted: HTMLElement;
    private legend_hidden: HTMLElement;

    private shift_blocks: HTMLElement[];
    private slot_name_group: HTMLElement;
    private filter_legend: HTMLElement;

    private current_status_filter: HTMLInputElement;
    private current_slot_filter: HTMLInputElement;

    constructor() {
        window.addEventListener('load', () => {
            this.init();
        });
    }

    private init() {
        this.legend_highlighted = document.getElementById("legend-highlighted");
        this.legend_highlighted.classList.add(this.HIGHLIGHT_CLASS);
        this.legend_hidden = document.getElementById("legend-hidden");
        this.legend_hidden.classList.add(this.HIDDEN_CLASS);
        this.filter_legend = document.getElementById("filter-legend");
        this.slot_name_group = document.getElementById("slot-name-group")
        this.shift_blocks = Array.from(document.getElementsByClassName("shift-block") as HTMLCollectionOf<HTMLElement>);

        for (let slot_status_button of document.getElementsByName("slot_status_options") as NodeListOf<HTMLInputElement>) {
            if (slot_status_button.classList.contains("active-on-load")) {
                this.current_status_filter = slot_status_button as HTMLInputElement;
                slot_status_button.click();
            }
            slot_status_button.addEventListener("click", () => {
                this.current_status_filter = slot_status_button;
                this.on_filter_changed();
            });
        }

        for (let slot_name_button of document.getElementsByName("slot_name_options") as NodeListOf<HTMLInputElement>) {
            if (slot_name_button.classList.contains("active-on-load")) {
                this.current_slot_filter = slot_name_button as HTMLInputElement;
                slot_name_button.click();
            }
            slot_name_button.addEventListener("click", () => {
                this.current_slot_filter = slot_name_button;
                this.on_filter_changed();
            });
        }

        this.on_filter_changed();
    }

    private on_filter_changed() {
        for (let shift_block of this.shift_blocks) {
            this.update_shift_block(shift_block, this.current_status_filter.value as StatusFilter, this.current_slot_filter.value);
        }

        this.legend_highlighted.innerText = this.current_status_filter.parentElement.innerText;
        if (this.current_status_filter.value == StatusFilter.FREESLOT) {
            this.legend_highlighted.innerText += " - " + this.current_slot_filter.parentElement.innerText;
        }

        this.slot_name_group.style.display = this.current_status_filter.value == StatusFilter.FREESLOT ? null : "none";
        this.filter_legend.style.display = this.current_status_filter.value != StatusFilter.NO_FILTER ? null : "none";
    }

    private update_shift_block(shift_block: HTMLElement, slot_status_filter: StatusFilter, slot_name_filter: string) {
        shift_block.classList.remove(this.HIDDEN_CLASS);
        shift_block.classList.remove(this.NO_FILTER_CLASS);
        shift_block.classList.remove(this.HIGHLIGHT_CLASS);

        let addedClass: string;
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

new ShiftFiltersManager();
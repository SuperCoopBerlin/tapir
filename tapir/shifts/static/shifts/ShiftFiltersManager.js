var StatusFilter;
(function (StatusFilter) {
    StatusFilter["FREESLOT"] = "free-slot";
    StatusFilter["NO_FILTER"] = "no-filter";
    StatusFilter["NEEDS_HELP"] = "needs-help";
})(StatusFilter || (StatusFilter = {}));
var ShiftFiltersManager = /** @class */ (function () {
    function ShiftFiltersManager() {
        var _this = this;
        this.HIDDEN_CLASS = "btn-light";
        this.NO_FILTER_CLASS = "btn-outline-dark";
        this.HIGHLIGHT_CLASS = "btn-info";
        this.CANCELLED_CLASS = "btn-secondary";
        window.addEventListener('load', function () {
            _this.init();
        });
    }
    ShiftFiltersManager.prototype.init = function () {
        var _this = this;
        this.legend_highlighted = document.getElementById("legend-highlighted");
        this.legend_highlighted.classList.add(this.HIGHLIGHT_CLASS);
        var legend_hidden = document.getElementById("legend-hidden");
        legend_hidden.classList.add(this.HIDDEN_CLASS);
        var legend_cancelled = document.getElementById("legend-cancelled");
        legend_cancelled.classList.add(this.CANCELLED_CLASS);
        this.filter_legend = document.getElementById("filter-legend");
        this.slot_name_group = document.getElementById("slot-name-group");
        this.shift_blocks = Array.from(document.getElementsByClassName("shift-block"));
        var _loop_1 = function (slot_status_button) {
            if (slot_status_button.classList.contains("active-on-load")) {
                this_1.current_status_filter = slot_status_button;
                slot_status_button.click();
            }
            slot_status_button.addEventListener("click", function () {
                _this.current_status_filter = slot_status_button;
                _this.on_filter_changed();
            });
        };
        var this_1 = this;
        for (var _i = 0, _a = document.getElementsByName("slot_status_options"); _i < _a.length; _i++) {
            var slot_status_button = _a[_i];
            _loop_1(slot_status_button);
        }
        var _loop_2 = function (slot_name_button) {
            if (slot_name_button.classList.contains("active-on-load")) {
                this_2.current_slot_filter = slot_name_button;
                slot_name_button.click();
            }
            slot_name_button.addEventListener("click", function () {
                _this.current_slot_filter = slot_name_button;
                _this.on_filter_changed();
            });
        };
        var this_2 = this;
        for (var _b = 0, _c = document.getElementsByName("slot_name_options"); _b < _c.length; _b++) {
            var slot_name_button = _c[_b];
            _loop_2(slot_name_button);
        }
        this.on_filter_changed();
    };
    ShiftFiltersManager.prototype.on_filter_changed = function () {
        for (var _i = 0, _a = this.shift_blocks; _i < _a.length; _i++) {
            var shift_block = _a[_i];
            this.update_shift_block(shift_block, this.current_status_filter.value, this.current_slot_filter.value);
        }
        this.legend_highlighted.innerText = this.current_status_filter.nextElementSibling.innerHTML;
        if (this.current_status_filter.value == StatusFilter.FREESLOT) {
            this.legend_highlighted.innerText += " - " + this.current_slot_filter.nextElementSibling.innerHTML;
        }
        this.slot_name_group.style.display = this.current_status_filter.value == StatusFilter.FREESLOT ? null : "none";
    };
    ShiftFiltersManager.prototype.update_shift_block = function (shift_block, slot_status_filter, slot_name_filter) {
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
        var addedClass;
        switch (slot_status_filter) {
            case StatusFilter.NO_FILTER:
                addedClass = this.NO_FILTER_CLASS;
                break;
            case StatusFilter.NEEDS_HELP:
                addedClass = shift_block.classList.contains("needs_help") ? this.HIGHLIGHT_CLASS : this.HIDDEN_CLASS;
                break;
            case StatusFilter.FREESLOT:
                var filtered_class = "freeslot_" + slot_name_filter;
                addedClass = shift_block.classList.contains(filtered_class) ? this.HIGHLIGHT_CLASS : this.HIDDEN_CLASS;
                break;
        }
        shift_block.classList.add(addedClass);
    };
    return ShiftFiltersManager;
}());
var shiftFilterManager = new ShiftFiltersManager();

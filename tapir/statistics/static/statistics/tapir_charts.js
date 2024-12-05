var ChartManager = /** @class */ (function () {
    function ChartManager() {
    }
    ChartManager.prototype.register_show_chart_button = function (button, url, canvas_id) {
        var _this = this;
        button.addEventListener('click', function () {
            _this.show_stats_chart(button, url, canvas_id);
        });
        button.addEventListener('keydown', function (event) {
            if (event.key === 'Tab')
                return;
            _this.show_stats_chart(button, url, canvas_id);
        });
    };
    ChartManager.prototype.show_stats_chart = function (button, url, canvas_id) {
        var _this = this;
        var buttonText = button.getElementsByClassName("button-text")[0];
        buttonText.innerText = "Loading...";
        fetch(url)
            .then(function (response) {
            if (response.ok) {
                return response.json();
            }
            return Promise.reject(response);
        })
            .then(function (data) {
            _this.on_data_loaded(data, button, canvas_id);
        })
            .catch(function (response) {
            _this.on_load_error(response, button);
        });
    };
    ChartManager.prototype.on_data_loaded = function (data, button, canvas_id) {
        button.style.display = "none";
        var canvas = document.getElementById(canvas_id);
        canvas.style.display = null;
        new Chart(canvas, data);
    };
    ChartManager.prototype.on_load_error = function (response, button) {
        console.log(response);
        var buttonText = button.getElementsByClassName("button-text")[0];
        buttonText.innerText = "Error";
        var icon = button.getElementsByClassName("material-icons")[0];
        icon.innerText = "error";
        button.classList.remove("btn-outline-secondary");
        button.classList.add("btn-outline-danger");
        button.classList.add("disabled");
        console.error(response.name, response.message);
    };
    return ChartManager;
}());
var chartManager = new ChartManager();

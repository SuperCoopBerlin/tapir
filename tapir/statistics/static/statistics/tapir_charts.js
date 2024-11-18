class ChartManager {
    register_show_chart_button(button, url, canvas_id) {
        button.addEventListener('click', () => {
            this.show_stats_chart(button, url, canvas_id);
        });
        button.addEventListener('keydown', (event) => {
            if (event.key === 'Tab')
                return;
            this.show_stats_chart(button, url, canvas_id);
        });
    }
    show_stats_chart(button, url, canvas_id) {
        const buttonText = button.getElementsByClassName("button-text")[0];
        buttonText.innerText = "Loading...";
        fetch(url)
            .then(response => {
            if (response.ok) {
                return response.json();
            }
            return Promise.reject(response);
        })
            .then(data => {
            this.on_data_loaded(data, button, canvas_id);
        })
            .catch((response) => {
            this.on_load_error(response, button);
        });
    }
    on_data_loaded(data, button, canvas_id) {
        button.style.display = "none";
        const canvas = document.getElementById(canvas_id);
        canvas.style.display = null;
        new Chart(canvas, data);
    }
    on_load_error(response, button) {
        console.log(response);
        const buttonText = button.getElementsByClassName("button-text")[0];
        buttonText.innerText = "Error";
        const icon = button.getElementsByClassName("material-icons")[0];
        icon.innerText = "error";
        button.classList.remove("btn-outline-secondary");
        button.classList.add("btn-outline-danger");
        button.classList.add("disabled");
        console.error(response.name, response.message);
    }
}
let chartManager = new ChartManager();
//# sourceMappingURL=tapir_charts.js.map
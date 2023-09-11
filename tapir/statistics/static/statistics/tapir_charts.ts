class ChartManager {
    public show_stats_chart(button: HTMLElement, url: string, canvas_id: string) {
        const buttonText = button.getElementsByClassName("button-text")[0] as HTMLElement;
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

    private on_data_loaded(data: any, button: HTMLElement, canvas_id: string) {
        button.style.display = "none";
        const canvas = document.getElementById(canvas_id);
        canvas.style.display = null;
        new Chart(canvas, data);
    }


    private on_load_error(response: Error, button: HTMLElement) {
        console.log(response);
        const buttonText = button.getElementsByClassName("button-text")[0] as HTMLElement;
        buttonText.innerText = "Error";
        const icon = button.getElementsByClassName("material-icons")[0] as HTMLElement;
        icon.innerText = "error";
        button.classList.remove("btn-outline-secondary");
        button.classList.add("btn-outline-danger");
        button.classList.add("disabled");
        console.error(response.name, response.message);
    }
}

let chartManager = new ChartManager();
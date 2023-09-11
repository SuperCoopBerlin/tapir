def build_pie_chart_data(labels: list, data: list):
    return {
        "type": "pie",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": " ",
                    "data": data,
                },
            ],
        },
    }


def build_line_chart_data(x_axis_values: list, y_axis_values: list, data_label: str):
    return {
        "type": "line",
        "data": {
            "labels": x_axis_values,
            "datasets": [
                {
                    "label": data_label,
                    "data": y_axis_values,
                }
            ],
        },
    }

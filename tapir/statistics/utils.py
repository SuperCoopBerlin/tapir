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


def build_line_chart_data(
    x_axis_values: list,
    y_axis_values: list,
    data_label: str,
    y_axis_max: float | None = None,
):
    data = {
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
    if y_axis_max:
        data["options"] = {"scales": {"y": {"max": y_axis_max}}}
    return data

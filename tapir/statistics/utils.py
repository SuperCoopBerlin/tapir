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
    data_labels: list,
    y_axis_min: float | None = None,
    y_axis_max: float | None = None,
    stacked=False,
):
    data = {
        "type": "line",
        "data": {
            "labels": x_axis_values,
            "datasets": [],
        },
        "options": {
            "scales": {
                "y": {
                    "min": y_axis_min,
                    "max": y_axis_max,
                    "stacked": stacked,
                }
            }
        },
    }

    for index, values in enumerate(y_axis_values):
        data["data"]["datasets"].append(
            {
                "label": data_labels[index],
                "data": values,
                "fill": stacked,
            }
        )

    return data


def build_bar_chart_data(labels: list, data: list, label: str | None = " "):
    return {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": label,
                    "data": data,
                    "backgroundColor": [
                        "rgba(154, 208, 245, 1)",
                    ],
                },
            ],
        },
    }

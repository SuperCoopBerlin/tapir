from tapir.configuration.models import (
    TapirParameterDatatype,
    TapirParameterDefinitionImporter,
)
from tapir.configuration.parameter import parameter_definition, ParameterMeta


class ParameterCategory:
    COOP = "Coop"


class Parameter:
    COOP_NAME = "tapir.coop.name"
    LOGO_BASE64 = "tapir.coop.logo_base64"
    CUSTOM_PDF_CSS = "tapir.coop.pdf_css"
    CUSTOM_WEB_CSS = "tapir.coop.web_css"


class ParameterDefinitions(TapirParameterDefinitionImporter):
    def import_definitions(self):
        parameter_definition(
            key=Parameter.COOP_NAME,
            datatype=TapirParameterDatatype.STRING,
            initial_value="SuperCoop Berlin eG",
            description="",
            category=ParameterCategory.COOP,
            order_priority=1000,
            label="Name of cooperative",
        )

        parameter_definition(
            key=Parameter.LOGO_BASE64,
            datatype=TapirParameterDatatype.STRING,
            initial_value="",
            description="Logo of organization encoded in base64.",
            category=ParameterCategory.COOP,
            order_priority=900,
            label="Coop Logo",
            meta=ParameterMeta(
                textarea=True,
            ),
        )

        parameter_definition(
            key=Parameter.CUSTOM_PDF_CSS,
            datatype=TapirParameterDatatype.STRING,
            initial_value="",
            description="",
            category=ParameterCategory.COOP,
            order_priority=900,
            label="Custom CSS for PDF creation",
            meta=ParameterMeta(
                textarea=True,
            ),
        )

        parameter_definition(
            key=Parameter.CUSTOM_WEB_CSS,
            datatype=TapirParameterDatatype.STRING,
            initial_value="",
            description="",
            category=ParameterCategory.COOP,
            order_priority=900,
            label="Custom CSS for website",
            meta=ParameterMeta(
                textarea=True,
            ),
        )

__copyright__ = 'Copyright 2024, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

from pathlib import Path
from typing import List

from qgis.core import (
    Qgis,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextScope,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsMessageLog,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication

from dynamic_layers.definitions import PLUGIN_MESSAGE

""" Tools to work with resources files. """


def string_substitution(
        input_string: str,
        variables: dict,
        project: QgsProject = None,
        layer: QgsVectorLayer = None,
        feature: QgsFeature = None,
        is_template: bool = False,
        feedback: QgsProcessingFeedback = None,
) -> str:
    """ String substitution. """
    msg = tr(
        "Evaluation of the expression '{expression}' \n"
        "with variables :\n").format(expression=input_string)

    scope = QgsExpressionContextScope()
    for key, value in variables.items():
        scope.addVariable(QgsExpressionContextScope.StaticVariable(key, value, True, True))
        msg += f"→ {key} = {value}\n"

    context = QgsExpressionContext()
    # noinspection PyArgumentList
    context.appendScope(QgsExpressionContextUtils.globalScope())

    msg += tr("and project {project}\n").format(project=project.fileName() if project else "empty")
    if project:
        # noinspection PyArgumentList
        context.appendScope(QgsExpressionContextUtils.projectScope(project))

    msg += tr("and layer {layer}\n").format(layer=layer.name() if layer else "empty")
    if layer:
        # noinspection PyArgumentList
        context.appendScope(QgsExpressionContextUtils.layerScope(layer))

    msg += tr("and feature {feature}\n").format(feature=feature.id() if feature else "empty")
    if feature:
        context.setFeature(feature)

    context.appendScope(scope)

    log(msg, Qgis.Info, feedback)

    if is_template:
        # noinspection PyArgumentList
        output = QgsExpression.replaceExpressionText(input_string, context)
        return output

    expression = QgsExpression(input_string)
    if expression.hasEvalError() or expression.hasParserError():
        raise QgsProcessingException(tr("Invalid QGIS expression : {}").format(input_string))

    output = expression.evaluate(context)
    msg = tr("Output is {}").format(output)
    log(msg, Qgis.Info, feedback)

    return output


def log(msg: str, level: Qgis.MessageLevel = Qgis.Info, feedback: QgsProcessingFeedback = None):
    """ Log a message, either in the log panel, or in the Processing UI panel. """
    if feedback:
        if level == Qgis.Warning:
            feedback.reportError(msg)
        elif level == Qgis.Critical:
            feedback.reportError(msg)
        elif level == Qgis.Info:
            feedback.pushDebugInfo(msg)
        elif level == Qgis.Success:
            feedback.pushInfo(msg)
        else:
            feedback.pushDebugInfo(msg)
    else:
        # noinspection PyTypeChecker
        QgsMessageLog.logMessage(msg, PLUGIN_MESSAGE, level)


def plugin_path(*args) -> Path:
    """Return the path to the plugin root folder."""
    path = Path(__file__).resolve().parent
    for item in args:
        path = path.joinpath(item)

    return path


def resources_path(*args) -> Path:
    """Return the path to the plugin resources folder."""
    return plugin_path("resources", *args)


def side_car_files(file_path: Path) -> List[Path]:
    """ Return a list of all side-car files, having the extension included. """
    results = []
    for iter_file in file_path.parent.iterdir():
        if iter_file.name.startswith(file_path.name) and iter_file != file_path:
            results.append(iter_file)

    results.sort()
    return results


def tr(message: str) -> str:
    return QCoreApplication.translate('DynamicLayers', message)

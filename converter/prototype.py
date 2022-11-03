import utils
from .context import context
from sketchformat.prototype import *

OVERLAY_INTERACTION = {
    'NONE': OverlayBackgroundInteraction.NONE,
    'CLOSE_ON_CLICK_OUTSIDE': OverlayBackgroundInteraction.CLOSES_OVERLAY
}

ANIMATION_TYPE = {
    'INSTANT_TRANSITION': AnimationType.NONE,
    'SLIDE_FROM_LEFT': AnimationType.SLIDE_FROM_LEFT,
    'SLIDE_FROM_RIGHT': AnimationType.SLIDE_FROM_RIGHT,
    'SLIDE_FROM_TOP': AnimationType.SLIDE_FROM_TOP,
    'SLIDE_FROM_BOTTOM': AnimationType.SLIDE_FROM_BOTTOM,
    'PUSH_FROM_LEFT': AnimationType.SLIDE_FROM_LEFT,
    'PUSH_FROM_RIGHT': AnimationType.SLIDE_FROM_RIGHT,
    'PUSH_FROM_TOP': AnimationType.SLIDE_FROM_TOP,
    'PUSH_FROM_BOTTOM': AnimationType.SLIDE_FROM_BOTTOM,
    'MOVE_FROM_LEFT': AnimationType.SLIDE_FROM_LEFT,
    'MOVE_FROM_RIGHT': AnimationType.SLIDE_FROM_RIGHT,
    'MOVE_FROM_TOP': AnimationType.SLIDE_FROM_TOP,
    'MOVE_FROM_BOTTOM': AnimationType.SLIDE_FROM_BOTTOM,
    'SLIDE_OUT_TO_LEFT': AnimationType.SLIDE_FROM_LEFT,
    'SLIDE_OUT_TO_RIGHT': AnimationType.SLIDE_FROM_RIGHT,
    'SLIDE_OUT_TO_TOP': AnimationType.SLIDE_FROM_TOP,
    'SLIDE_OUT_TO_BOTTOM': AnimationType.SLIDE_FROM_BOTTOM,
    'MOVE_OUT_TO_LEFT': AnimationType.SLIDE_FROM_LEFT,
    'MOVE_OUT_TO_RIGHT': AnimationType.SLIDE_FROM_RIGHT,
    'MOVE_OUT_TO_TOP': AnimationType.SLIDE_FROM_TOP,
    'MOVE_OUT_TO_BOTTOM': AnimationType.SLIDE_FROM_BOTTOM,
    'MAGIC_MOVE': AnimationType.NONE,
    'SMART_ANIMATE': AnimationType.NONE,
    'SCROLL_ANIMATE': AnimationType.NONE,
}


# TODO: Is this called from every node type (groups?)
def convert_flow(figma_node):
    # TODO: What happens with multiple actions?
    flow = None
    for interaction in figma_node.get('prototypeInteractions', []):
        if interaction['isDeleted']:
            continue

        if interaction['event']['interactionType'] != 'ON_CLICK':
            print('Unsupported interaction type')
            continue

        for action in interaction['actions']:
            # Figma sometimes keeps empty interactions in the model, we just ignore them
            if action == {}:
                continue

            # TODO: Back is SCROLL for some reason??? or just irrelevant?
            if action['navigationType'] not in ['NAVIGATE', 'SCROLL', 'OVERLAY']:
                print('Unsupported action type')
                continue

            if flow is not None:
                print('Unsupported multiple actions per layer')
                continue

            if action['connectionType'] not in ['BACK', 'INTERNAL_NODE', 'NONE']:
                print(f"Unsupported connection type {action['connectionType']}")
                continue

            destination, overlay_settings = get_destination_settings_if_any(action)

            flow = FlowConnection(
                destinationArtboardID=destination,
                animationType=ANIMATION_TYPE[action.get('transitionType', 'INSTANT_TRANSITION')],
                maintainScrollPosition=action.get('transitionPreserveScroll', False),
                overlaySettings=overlay_settings
            )

    return {'flow': flow} if flow else {}


def prototyping_information(figma_frame):
    # Some information about the prototype is in the Figma page
    figma_canvas = context.figma_node(figma_frame['parent']['guid'])
    if 'prototypeDevice' not in figma_canvas:
        return {
            'isFlowHome': False,
            'overlayBackgroundInteraction': 0,
            'presentationStyle': 0
        }

    # TODO: Overflow scrolling means making the artboard bigger (fit the child bounds)
    if figma_frame.get('scrollDirection', 'NONE') != 'NONE':
        print('Scroll overflow direction not supported')

    if 'overlayBackgroundInteraction' in figma_frame:
        obj = {
            'overlayBackgroundInteraction': OVERLAY_INTERACTION[
                figma_frame['overlayBackgroundInteraction']],
            'presentationStyle': PresentationStyle.OVERLAY,
            'overlaySettings': FlowOverlaySettings.Positioned(
                figma_frame.get('overlayPositionType', 'CENTER'))
        }
    else:
        obj = {
            'isFlowHome': figma_frame.get('prototypeStartingPoint', {}).get('name', '') != '',
            'prototypeViewport': PrototypeViewport(
                name=figma_canvas['prototypeDevice']['presetIdentifier'],
                size=utils.point_to_string(figma_canvas['prototypeDevice']['size'])
            ),
            'overlayBackgroundInteraction': OverlayBackgroundInteraction.NONE,
            'presentationStyle': PresentationStyle.SCREEN,
            'overlaySettings': FlowOverlaySettings.RegularArtboard()
        }

    return obj


def get_destination_settings_if_any(action):
    overlay_settings = None

    match action['connectionType'], action.get('transitionNodeID', None):
        case 'BACK', _:
            destination = 'back'
        case 'INTERNAL_NODE', None:
            destination = None
        case 'INTERNAL_NODE', transition_node_id:
            destination = utils.gen_object_id(transition_node_id)
            transition_node = context.figma_node(transition_node_id)

            if 'overlayBackgroundInteraction' in transition_node:
                overlay_settings = FlowOverlaySettings.Positioned(
                    transition_node.get('overlayPositionType', 'CENTER'))

        case 'NONE', _:
            destination = None
        case _:
            print(f"Unsupported connection type {action['connectionType']}")
            return

    return destination, overlay_settings

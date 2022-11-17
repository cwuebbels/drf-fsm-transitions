from rest_framework.decorators import action
from rest_framework.response import Response


def get_transition_viewset_method(transition_name, **kwargs):
    '''
    Create a viewset method for the provided `transition_name`
    '''
    def inner_func(self, request, pk=None, **kwargs):
        object = self.get_object()
        transition_method = getattr(object, transition_name)

        transition_method(by=self.request.user, request=request, **kwargs)

        if self.save_after_transition:
            object.save()

        serializer = self.get_serializer(object)
        return Response(serializer.data)

    inner_func.__name__ = transition_name

    try:
        inner_func.mapping = dict.fromkeys(inner_func.mapping, transition_name)
    except AttributeError:
        pass

    return inner_func


def get_viewset_transition_action_mixin(model, field='state', transition_names=None, **kwargs):
    '''
    Find all transitions defined on `model`, then create a corresponding
    viewset action method for each and apply it to `Mixin`. Finally, return
    `Mixin`
    '''
    class Mixin(object):
        save_after_transition = True

    if not transition_names:
        transitions = getattr(model(), f'get_all_{field}_transitions')()
        transition_names = set(x.name for x in transitions)

    for transition_name in transition_names:
        url_name = transition_name.replace('_', '-')
        setattr(
            Mixin,
            transition_name,
            action(methods=['POST'], detail=True, url_name=url_name, url_path=transition_name)(
                get_transition_viewset_method(transition_name)
            ),
        )

    return Mixin

from wagtail.wagtailcore import hooks

from .menu import ApprovalMenuItem

@hooks.register('construct_main_menu')
def construct_main_menu(request, menu_items):
    menu_items.append(ApprovalMenuItem())


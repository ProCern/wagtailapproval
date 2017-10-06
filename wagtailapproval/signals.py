from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.dispatch import Signal

step_published = Signal(providing_args=[
    'instance'])

pipeline_published = Signal(providing_args=[
    'instance'])

build_approval_item_list = Signal(providing_args=[
    'approval_step',
    'user'])

remove_approval_items = Signal(providing_args=[
    'approval_items',
    'user'])

set_collection_edit = Signal(providing_args=[
    'approval_step',
    'edit'])

take_ownership = Signal(providing_args=[
    'approval_step',
    'object',
    'pipeline'])

release_ownership = Signal(providing_args=[
    'approval_step',
    'object',
    'pipeline'])

pre_transfer_ownership = Signal(providing_args=[
    'giving_step',
    'taking_step',
    'object',
    'pipeline'])

post_transfer_ownership = Signal(providing_args=[
    'giving_step',
    'taking_step',
    'object',
    'pipeline'])

pre_approve = Signal(providing_args=[
    'giving_step',
    'taking_step',
    'object',
    'pipeline'])

post_approve = Signal(providing_args=[
    'giving_step',
    'taking_step',
    'object',
    'pipeline'])

pre_reject = Signal(providing_args=[
    'giving_step',
    'taking_step',
    'object',
    'pipeline'])

post_reject = Signal(providing_args=[
    'giving_step',
    'taking_step',
    'object',
    'pipeline'])

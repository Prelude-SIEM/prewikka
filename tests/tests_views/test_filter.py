# Copyright (C) 2018 CS-SI. All Rights Reserved.
#
# This file is part of the Prewikka program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Tests for `prewikka.views.filter`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import copy

import pytest

from prewikka import hookmanager
from prewikka.dataprovider import Criterion
from prewikka.error import PrewikkaUserError
from tests.utils.fixtures import load_view_for_fixtures


@pytest.fixture(scope='function')
def filter_fixtures(request):
    """
    Fixture for filter tests.

    :return: view for filter.
    :rtype: prewikka.view.View
    """
    from prewikka.views.filter.filter import FilterDatabase, Filter  # prevent import error

    view = load_view_for_fixtures(request.param)
    view.process_parameters()

    database = FilterDatabase()

    criterion_1 = Criterion('alert.messageid', '=', 'fakemessageid1')
    criteria_1 = {'alert': criterion_1}
    filter_obj_1 = Filter(None, 'Test filter 1', 'Filter description', criteria_1)
    database.upsert_filter(env.request.user, filter_obj_1)

    criterion_2 = Criterion('heartbeat.messageid', '=', 'fakemessageid1')
    criteria_2 = {'heartbeat': criterion_2}
    filter_obj_2 = Filter(None, 'Test filter 2', 'Filter description', criteria_2)
    database.upsert_filter(env.request.user, filter_obj_2)

    criterion_3 = Criterion(criterion_1, '||', criterion_2)
    criteria_3 = {'alert': criterion_3}
    filter_obj_3 = Filter(None, 'Test filter 3', 'Filter description', criteria_3)
    database.upsert_filter(env.request.user, filter_obj_3)

    # complex criterion
    criterion_4 = Criterion(criterion_3, '||', criterion_2)
    criteria_4 = {'alert': criterion_4}
    filter_obj_4 = Filter(None, 'Test filter 4', 'Filter description', criteria_4)
    database.upsert_filter(env.request.user, filter_obj_4)

    def tear_down():
        """
        TearDown
        """
        env.db.query('DELETE FROM Prewikka_Filter')

    request.addfinalizer(tear_down)

    return {
        'view': view,
        'database': database,
        'filter_obj_1': filter_obj_1,
        'filter_obj_2': filter_obj_2,
        'filter_obj_3': filter_obj_3,
        'filter_obj_4': filter_obj_4,
        'criterion_list': [criterion_1, criterion_2, criterion_3, criterion_4]
    }


@pytest.mark.parametrize("filter_fixtures", ["filterview.listing"], indirect=True)
def test_filter_database(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterDatabase` class.

    Only test methods not already tested in views tests below.
    """
    database = filter_fixtures.get('database')

    assert database.get_filters(env.request.user, ftype='alert')

    # delete_filter()
    assert database.delete_filter(env.request.user)
    assert not database.delete_filter(env.request.user)  # second time to match special condition (no rows)


@pytest.mark.parametrize("filter_fixtures", ["filterview.listing"], indirect=True)
def test_listing(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.listing` view.
    """
    view = filter_fixtures.get('view')

    assert view.render()


@pytest.mark.parametrize("filter_fixtures", ["filterview.edit"], indirect=True)
def test_edit(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.edit` view.
    """
    view = filter_fixtures.get('view')

    assert view.render()


@pytest.mark.parametrize("filter_fixtures", ["filterview.edit"], indirect=True)
def test_edit_with_name(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.edit` view.
    """
    view = filter_fixtures.get('view')

    filter_obj_1 = filter_fixtures.get('filter_obj_1')
    filter_obj_2 = filter_fixtures.get('filter_obj_2')
    filter_obj_3 = filter_fixtures.get('filter_obj_3')
    filter_obj_4 = filter_fixtures.get('filter_obj_4')

    assert view.render(filter_obj_1.name)
    assert view.render(filter_obj_2.name)
    assert view.render(filter_obj_3.name)
    assert view.render(filter_obj_4.name)


@pytest.mark.parametrize("filter_fixtures", ["filterview.edit"], indirect=True)
def test_edit_duplicate(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.edit` view.
    """
    view = filter_fixtures.get('view')

    filter_obj_1 = filter_fixtures.get('filter_obj_1')
    env.request.parameters['duplicate'] = filter_obj_1.name

    assert view.render()


@pytest.mark.parametrize("filter_fixtures", ["filterview.delete"], indirect=True)
def test_delete(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.delete` view.
    """
    view = filter_fixtures.get('view')

    filter_obj_1 = filter_fixtures.get('filter_obj_1')
    env.request.parameters['id'] = [filter_obj_1.name]
    database = filter_fixtures.get('database')
    filter_count = len(filter_fixtures.get('criterion_list'))

    view.render()

    assert len(list(database.get_filters(env.request.user))) == filter_count - 1


@pytest.mark.parametrize("filter_fixtures", ["filterview.save"], indirect=True)
def test_save(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.save` view.

    save() without prior name (new filter)
    """
    view = filter_fixtures.get('view')

    env.request.parameters['filter_name'] = 'New name'
    env.request.parameters['types'] = ['heartbeat', 'alert']
    env.request.parameters['criteria'] = filter_fixtures.get('criterion_list')
    database = filter_fixtures.get('database')
    filter_count = len(filter_fixtures.get('criterion_list'))

    assert view.render()

    assert len(list(database.get_filters(env.request.user))) == filter_count + 1


@pytest.mark.parametrize("filter_fixtures", ["filterview.save"], indirect=True)
def test_save_without_name(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.save` view.

    save() without filter name specified.
    """
    view = filter_fixtures.get('view')

    env.request.parameters['types'] = ['heartbeat', 'alert']
    env.request.parameters['criteria'] = filter_fixtures.get('criterion_list')

    with pytest.raises(PrewikkaUserError):
        view.render()


@pytest.mark.parametrize("filter_fixtures", ["filterview.save"], indirect=True)
def test_save_rename(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.save` view.

    save() with a name change
    """
    view = filter_fixtures.get('view')

    env.request.parameters['filter_old_name'] = 'Test filter 1'
    env.request.parameters['filter_name'] = 'New name'
    env.request.parameters['types'] = ['heartbeat', 'alert']
    env.request.parameters['criteria'] = filter_fixtures.get('criterion_list')
    database = filter_fixtures.get('database')
    filter_count = len(filter_fixtures.get('criterion_list'))

    assert view.render()

    # ensure the filter is edited and not duplicated
    assert len(list(database.get_filters(env.request.user))) == filter_count


@pytest.mark.parametrize("filter_fixtures", ["filterview.save"], indirect=True)
def test_save_duplicated_name(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.save` view.

    save() with a duplicated name.
    """
    view = filter_fixtures.get('view')

    filter_obj_1 = filter_fixtures.get('filter_obj_1')
    env.request.parameters['filter_name'] = filter_obj_1.name
    env.request.parameters['types'] = ['heartbeat', 'alert']
    env.request.parameters['criteria'] = filter_fixtures.get('criterion_list')

    with pytest.raises(PrewikkaUserError):
        view.render()


@pytest.mark.parametrize("filter_fixtures", ["filterview.save"], indirect=True)
def test_save_update(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView.save` view.

    save() without changing the name.
    """
    view = filter_fixtures.get('view')

    filter_obj_1 = filter_fixtures.get('filter_obj_1')
    env.request.parameters['filter_name'] = filter_obj_1.name
    env.request.parameters['filter_old_name'] = filter_obj_1.name
    env.request.parameters['types'] = ['heartbeat', 'alert']
    env.request.parameters['criteria'] = filter_fixtures.get('criterion_list')

    assert view.render()


@pytest.mark.parametrize("filter_fixtures", ["filterview.listing"], indirect=True)
def test_hook_user_delete(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView._user_delete` hook.
    """
    list(hookmanager.trigger('HOOK_USER_DELETE', env.request.user))


@pytest.mark.parametrize("filter_fixtures", ["filterview.listing"], indirect=True)
def test_hook_filter_param_register(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView._filter_parameters_register` hook.
    """
    assert list(hookmanager.trigger('HOOK_MAINMENU_PARAMETERS_REGISTER', env.request.parameters))


@pytest.mark.parametrize("filter_fixtures", ["filterview.listing"], indirect=True)
def test_hook_filter_get_criteria(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView._filter_get_criteria` hook.
    """
    # default
    assert list(hookmanager.trigger('HOOK_DATAPROVIDER_CRITERIA_PREPARE', 'alert'))

    # env.request.menu = None
    backup_menu = copy(env.request.menu)
    env.request.menu = None

    assert list(hookmanager.trigger('HOOK_DATAPROVIDER_CRITERIA_PREPARE', 'alert'))

    env.request.menu = backup_menu

    # env.request.parameters.filter != None (invalid)
    env.request.parameters['filter'] = 'foo'

    assert list(hookmanager.trigger('HOOK_DATAPROVIDER_CRITERIA_PREPARE', 'alert'))

    # env.request.parameters.filter != None (valid)
    filter_obj_1 = filter_fixtures.get('filter_obj_1')
    env.request.parameters['filter'] = filter_obj_1.name

    assert list(hookmanager.trigger('HOOK_DATAPROVIDER_CRITERIA_PREPARE', 'alert'))


@pytest.mark.parametrize("filter_fixtures", ["filterview.listing"], indirect=True)
def test_filter_html_menu(filter_fixtures):
    """
    Test `prewikka.views.filter.filter.FilterView._filter_html_menu` hook.
    """
    assert list(hookmanager.trigger('HOOK_MAINMENU_EXTRA_CONTENT', 'alert', env.request.parameters, input_size="md"))

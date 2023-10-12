"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""


def test_create_form(news_admin_client, item):
    url = f'/news/for_item/{item.id}/create'
    response = news_admin_client.get(url)
    assert response.status_code == 200

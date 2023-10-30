========
HAV AURA
========

Aura introduces endpoint for collecting metadata about system. Authentication is done via API key.
In current implementation following information is returned:

* user count
* list of installed modules
* expiration information - values of system parameters ``database.expiration_date`` and ``database.expiration_reason``

Configuration
-------------
Add api key to ``odoo.conf`` file in following format:

.. code-block::

    hav_metadata_token=my_api_key

Usage
-----
Send HTTP GET request on {host}/hav/metadata with URL query parameter ``api_key=my_api_key``. You will receive json
response with following data:

.. code-block::

    {
      "user_count": 2,
      "installed_modules": [
        "base",
        "sale",
        "stock",
        ...
      ]
      "expiration": {
        "date": "2023-01-01",
        "reason": "important reason"
      }
    }

Changelog
---------
16.0.1.0.0
~~~~~~~~~~
- added: /hav/metadata endpoint with token security
- added: user_count information
- added: installed_modules information
- added: expiration system parameter information

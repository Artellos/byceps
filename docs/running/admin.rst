Admin Application
=================

.. important:: Before continuing, make sure that the :doc:`virtual
   environment </installation/virtual-env>` is set up and activated.

To run the admin application with Flask's (insecure!) *development*
server for development purposes:

.. code-block:: sh

   (venv)$ BYCEPS_CONFIG=../config/development.toml APP_MODE=admin flask --debug run

The admin application should now be reachable at
`<http://127.0.0.1:5000>`_ (on Flask's standard port).

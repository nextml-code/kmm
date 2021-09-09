Welcome to kmm's documentation!
===============================

Minimalistic library for reading files in the kmm file format.

Install
=======

.. code-block::

    pip install kmm

Usage
=====

.. code-block:: python

    from pathlib import Path
    import kmm

    kmm_path = Path("...")
    header_path = Path("...")

    positions = kmm.Positions.read_sync_adjust(kmm_path, header_path)


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   positions
   header

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

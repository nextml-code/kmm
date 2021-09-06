Welcome to kw6's documentation!
===============================

Minimalistic library for reading files in the kw6 file format.

Install
=======

.. code-block::

    pip install kmm

Usage
=====

.. code-block:: python

    from pathlib import Path
    import kmm

    path = Path("...")
    header_path = Path("...")

    df = kmm.read(path, header_path)


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   read

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

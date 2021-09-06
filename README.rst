==========
kmm reader
==========

Minimalistic library for reading files in the kmm/kmm2 file format. 

Usage
=====

.. code-block:: python

    from pathlib import Path
    import kmm

    path = Path("...")
    header_path = Path("...")

    df = kmm.read(path, header_path)

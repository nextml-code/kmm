==========
kmm reader
==========

Minimalistic library for reading files in the kmm/kmm2 file format. 

Usage
=====

.. code-block:: python

    from pathlib import Path
    import kmm

    kmm_path = Path("...")
    header_path = Path("...")

    positions = kmm.Positions.from_paths(kmm_path, header_path)

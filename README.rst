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

    header = Header.from_path(header_path)
    positions = (
        kmm.Positions.from_path(kmm_path)
        .sync_frame_index(header)
        .geodetic()
    )

    # or, equivalently
    positions = kmm.Positions.read_sync_adjust(kmm_path, header_path)

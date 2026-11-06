import re
import warnings
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import validate_call
from sweref99 import projections

pattern = re.compile(r".+\[.+\]")
pattern2 = re.compile(r"CMAST")

# Norway ("Banenor") kmm2 files are identified by this token in the VER header
# line. Most store WGS84 latitude/longitude in the coordinate columns instead of
# SWEREF99 TM northing/easting; newer ones, under the same header, store
# projected metres (see is_degrees).
norway_header_token = "NorKmmToKmm"
tm = projections.make_transverse_mercator("SWEREF_99_TM")

expected_columns = [
    "code",
    "centimeter",
    "track_section",
    "kilometer",
    "meter",
    "track_lane",
    "1?",
    "2?",
    "3?",
    "4?",
    "northing",
    "easting",
    "contact_wire_material",
    "rail_model",
    "sliper_model",
    "between_stations",
    "5?",
    "6?",
    "7?",
    "8?",
    "max_speed",
    "datetime",
    "bearing",
    "linear_coordinate",
]
expected_dtypes = dict(
    centimeter=np.int64,
    track_section=str,
    kilometer=np.int32,
    meter=np.int32,
    track_lane=str,
    northing=np.float32,
    easting=np.float32,
)


# A share of rows above this that reads the other way than the file's
# medians makes the file mixed: it is converted by the majority, as before,
# with a warning, since some of its rows will be wrong either way.
mixed_share_warning = 0.01


def _fixed_coordinates(dataframe):
    """The coordinate pairs of rows with a fix: neither NaN nor 0,0 (no fix
    yet, in degrees and in metres alike)."""
    northing = dataframe["northing"].abs()
    easting = dataframe["easting"].abs()
    fixed = northing.notna() & easting.notna() & ((northing != 0) | (easting != 0))
    return northing[fixed], easting[fixed]


def is_degrees(dataframe):
    """
    Whether a Norway file's coordinate columns hold WGS84 degrees.

    The same converter version (``NorKmmToKmm2_1.03``) writes either degrees or
    projected metres, so the header cannot tell them apart; the values can. A
    latitude is at most 90 and a longitude at most 180, while a northing
    anywhere in Scandinavia is in the millions and an easting in the hundred
    thousands. The medians over rows with a fix decide, so neither a few
    malformed rows nor a stretch without a fix (0,0) can flip a file. The
    projected files are UTM zone 33N (ETRS89), whose projection parameters
    SWEREF99 TM shares, so they pass through unchanged.

    Warns when more than ``mixed_share_warning`` of the rows read the other
    way: such a file mixes degrees and metres.
    """
    northing, easting = _fixed_coordinates(dataframe)
    if len(northing) == 0:
        return True
    degrees = bool(northing.median() <= 90 and easting.median() <= 180)
    row_degrees = (northing <= 90) & (easting <= 180)
    disagreeing = int((row_degrees != degrees).sum())
    if disagreeing > mixed_share_warning * len(northing):
        warnings.warn(
            f"Norway kmm2 file mixes degrees and projected coordinates: {disagreeing} of "
            f"{len(northing)} rows read as {'metres' if degrees else 'degrees'}, converted "
            f"as {'degrees' if degrees else 'metres'}",
            stacklevel=2,
        )
    return degrees


def latlon_to_sweref(dataframe):
    """
    Norway kmm2 files store WGS84 latitude/longitude in the coordinate columns
    (parsed here into the ``northing``/``easting`` columns of the shared layout).
    Convert them to SWEREF99 TM northing/easting so the rest of the pipeline,
    including the geodetic transform, behaves identically to Swedish files.
    A file that already holds projected metres is returned as it is.
    """
    if len(dataframe) == 0 or not {"northing", "easting"}.issubset(dataframe.columns):
        return dataframe
    if not is_degrees(dataframe):
        return dataframe

    latitude = dataframe["northing"].to_numpy()
    longitude = dataframe["easting"].to_numpy()
    grid = [
        (np.nan, np.nan)
        if np.isnan(lat) or np.isnan(lon)
        else tm.geodetic_to_grid(float(lat), float(lon))
        for lat, lon in zip(latitude, longitude)
    ]
    dataframe["northing"] = np.array([n for n, _ in grid], dtype=np.float32)
    dataframe["easting"] = np.array([e for _, e in grid], dtype=np.float32)
    return dataframe


@validate_call
def read_kmm2(
    path: Path, raise_on_malformed_data: bool = True, replace_commas: bool = True
):
    skiprows = [
        index
        for index, line in enumerate(path.read_text(encoding="latin1").splitlines())
        if pattern.match(line) or pattern2.match(line)
    ]
    norway = False
    with open(path, "r", encoding="latin1") as f:
        line = f.readline()
        if line.startswith("VER"):
            skiprows = [0] + skiprows
            norway = norway_header_token in line
        elif raise_on_malformed_data and not line.startswith("POS"):
            raise ValueError("Malformed data, first line is not POS or VER")

    try:
        if replace_commas:
            with open(path, "r", encoding="latin1") as f:
                content = f.read()
            content = content.replace(",", ".")
            file_obj = StringIO(content)
        else:
            file_obj = path

        try:
            parser_kwargs = dict(
                sep="\t",
                encoding="latin1" if not replace_commas else None,
                header=None,
                skiprows=skiprows,
                low_memory=False,
            )
            n_columns = len(pd.read_csv(file_obj, **parser_kwargs).columns)

            # Reset file pointer to beginning for StringIO objects
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)

            if n_columns > len(expected_columns):
                columns = [f"{i+1}?" for i in range(len(expected_columns), n_columns)]
            elif n_columns < len(expected_columns):
                columns = expected_columns[:n_columns]
            else:
                columns = expected_columns

            dataframe = pd.read_csv(
                file_obj,
                **parser_kwargs,
                names=columns,
                dtype=expected_dtypes,
            )
            if norway:
                dataframe = latlon_to_sweref(dataframe)
            return dataframe
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=expected_columns)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise ValueError("Unable to parse kmm2 file, invalid csv.") from e


def test_patterns():
    assert pattern.match("Västerås central [Vå]")
    assert pattern2.match("CMAST   281-2B")


def test_extra_columns():
    read_kmm2(Path("tests/extra_columns.kmm2"))


def test_norway_latlon_to_sweref():
    # Norway ("Banenor") files store WGS84 lat/lon in the coordinate columns;
    # read_kmm2 must convert them to SWEREF99 TM northing/easting so the rest of
    # the pipeline (including .geodetic()) recovers the original coordinates.
    dataframe = read_kmm2(Path("tests/norway.kmm2"))
    assert len(dataframe) == 4
    # SWEREF99 TM: northing in the millions, easting in the hundred-thousands.
    assert (dataframe["northing"] > 6_000_000).all()
    assert (dataframe["easting"] > 100_000).all()

    latitude, longitude = tm.grid_to_geodetic(
        dataframe["northing"].iloc[0], dataframe["easting"].iloc[0]
    )
    assert abs(latitude - 59.9100025) < 1e-4
    assert abs(longitude - 10.7545870) < 1e-4


# northing, easting as 0.1.10 read tests/norway.kmm2 (converting
# unconditionally). A degrees file must still read exactly this way.
NORWAY_0_1_10 = [
    [6649001.5, 262665.96875],
    [6649001.0, 262666.78125],
    [6649000.5, 262667.625],
    [6649000.5, 262668.5],
]


def test_norway_degrees_unchanged_from_0_1_10():
    dataframe = read_kmm2(Path("tests/norway.kmm2"))
    expected = np.array(NORWAY_0_1_10, dtype=np.float32)
    actual = dataframe[["northing", "easting"]].to_numpy()
    assert actual.dtype == np.float32
    assert np.array_equal(actual, expected)


def test_norway_projected_coordinates_pass_through():
    # Trimmed from a 2026 Bane NOR file: projected metres under the same
    # NorKmmToKmm2_1.03 header. 0.1.10 converted these as degrees.
    dataframe = read_kmm2(Path("tests/norway_projected.kmm2"))
    assert len(dataframe) == 5
    assert abs(dataframe["northing"].iloc[0] - 6632290.739231621) < 1
    assert abs(dataframe["easting"].iloc[0] - 230493.47419632197) < 1

    latitude, longitude = tm.grid_to_geodetic(
        dataframe["northing"].iloc[0], dataframe["easting"].iloc[0]
    )
    # Bane NOR section 1420, west of Oslo.
    assert 59.5 < latitude < 60.2
    assert 10.0 < longitude < 11.0


def test_norway_degrees_2025_unchanged_from_0_1_10():
    # Every 600th row of a 2025 Bane NOR file in degrees, and the northing
    # and easting 0.1.10 read from it (written with kmm 0.1.10 from PyPI).
    dataframe = read_kmm2(Path("tests/norway_degrees_2025.kmm2"))
    expected = pd.read_csv("tests/norway_degrees_2025.expected-0.1.10.csv")
    assert np.array_equal(
        dataframe[["northing", "easting"]].to_numpy(),
        expected[["northing", "easting"]].to_numpy(dtype=np.float32),
    )


def test_norway_projected_with_rows_without_fix_stays_projected():
    # 3 of 5 rows at 0,0 (no fix yet) must not flip a projected file to degrees.
    projected = pd.DataFrame(
        {
            "northing": [0.0, 0.0, 0.0, 6632290.7, 6632291.2],
            "easting": [0.0, 0.0, 0.0, 230493.5, 230494.4],
        }
    )
    assert not is_degrees(projected)


def test_norway_mixed_file_warns():
    mixed = pd.DataFrame(
        {
            "northing": [59.91] * 90 + [6632290.7] * 10,
            "easting": [10.63] * 90 + [230493.5] * 10,
        }
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert is_degrees(mixed)
    assert any(
        "mixes degrees and projected" in str(warning.message) for warning in caught
    )


def test_norway_clean_file_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        read_kmm2(Path("tests/norway.kmm2"))
        read_kmm2(Path("tests/norway_projected.kmm2"))

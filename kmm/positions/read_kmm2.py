import re
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import validate_call
from sweref99 import projections

pattern = re.compile(r".+\[.+\]")
pattern2 = re.compile(r"CMAST")

# Norway ("Banenor") kmm2 files are identified by this token in the VER header
# line. Older ones store WGS84 latitude/longitude in the coordinate columns
# instead of SWEREF99 TM northing/easting; newer ones, under the same header,
# store projected northing/easting already.
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


def is_degrees(dataframe):
    """
    The same converter version (``NorKmmToKmm2_1.03``) writes either WGS84
    degrees or projected metres into the coordinate columns, so the header
    cannot tell them apart; the values can. A latitude is at most 90, while a
    northing anywhere in Scandinavia is in the millions. The projected files
    use zone 33 ETRS89 coordinates, which SWEREF99 TM shares its projection
    with, so they pass through unchanged.
    """
    northing = dataframe["northing"].abs()
    easting = dataframe["easting"].abs()
    return bool(northing.median() <= 90 and easting.median() <= 180)


def latlon_to_sweref(dataframe):
    """
    Norway kmm2 files store WGS84 latitude/longitude in the coordinate columns
    (parsed here into the ``northing``/``easting`` columns of the shared layout).
    Convert them to SWEREF99 TM northing/easting so the rest of the pipeline,
    including the geodetic transform, behaves identically to Swedish files.
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


def test_norway_projected_coordinates_pass_through():
    # Newer Norway files carry the same VER header but already store projected
    # northing/easting. Converting those as degrees produced garbage; they must
    # land on the same place as the lat/lon fixture (same four positions).
    projected = read_kmm2(Path("tests/norway_projected.kmm2"))
    degrees = read_kmm2(Path("tests/norway.kmm2"))
    assert len(projected) == 4
    assert np.allclose(projected["northing"], degrees["northing"], atol=1.0)
    assert np.allclose(projected["easting"], degrees["easting"], atol=1.0)

    latitude, longitude = tm.grid_to_geodetic(
        projected["northing"].iloc[0], projected["easting"].iloc[0]
    )
    assert abs(latitude - 59.9100025) < 1e-4
    assert abs(longitude - 10.7545870) < 1e-4

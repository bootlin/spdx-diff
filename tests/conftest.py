# SPDX-License-Identifier: GPL-2.0

import os
import pathlib
import subprocess
import tempfile
from collections.abc import Generator
from typing import Any

import pytest


@pytest.fixture(scope="session")
def sbom_data() -> Generator[pathlib.Path, None, None]:
    if path := os.environ.get("SBOM_DIFF_SBOM_DATA"):
        sbom_data_path = pathlib.Path(path).resolve()
        if sbom_data_path.is_dir():
            yield sbom_data_path
            return

    sbom_data_path = (
        pathlib.Path(__file__)
        .parent.parent.parent.joinpath("meta-sbom-diff-test", "sbom-data")
        .resolve()
    )
    if sbom_data_path.is_dir():
        yield sbom_data_path
        return

    pytest.exit(
        "The `sbom-data` directory was not found. To resolve this issue, "
        "please do one of the following: \n"
        " - Clone https://github.com/bootlin/meta-sbom-diff-test.git repository at the"
        " same directory level as the `sbom-diff` repository.\n"
        " - Set the `SBOM_DIFF_SBOM_DATA` environment variable to the path of"
        " `sbom-data` directory, contained in the `meta-sbom-diff-test` repository.",
        returncode=1,
    )


@pytest.fixture(scope="function")
def tmp_dir() -> Generator[pathlib.Path, None, None]:
    extra_opts: dict[str, Any] = {}
    if os.environ.get("SBOM_DIFF_TEST_KEEP_TMP") == "1":
        # The delete parameter was added in Python 3.12
        extra_opts["delete"] = False

    with tempfile.TemporaryDirectory(prefix="sbom-diff-", **extra_opts) as d:
        yield pathlib.Path(d)

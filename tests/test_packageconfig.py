# SPDX-License-Identifier: GPL-2.0

import pathlib

from helper import ExpectedDiff, run_spdx_diff_check


def test_cfg_changed(tmp_dir: pathlib.Path, sbom_data: pathlib.Path) -> None:
    exp = ExpectedDiff()
    exp.same_expect_ignore_proprietary = True
    exp.packageconfig_changed_mod("openssl", "no-tls1", "disabled", "enabled")

    run_spdx_diff_check(
        tmp_dir,
        sbom_data,
        "reference-sbom.spdx.json",
        "test-new-packageconfig.spdx.json",
        exp,
    )

# SPDX-License-Identifier: GPL-2.0

import pathlib

from helper import ExpectedDiff, run_sbom_diff_check


def test_new_version(tmp_dir: pathlib.Path, sbom_data: pathlib.Path) -> None:
    exp = ExpectedDiff()
    exp.same_expect_ignore_proprietary = True
    old_v = "6.6.111+git"
    new_v = "6.6.111-2"
    exp.package_changed("kernel", old_v, new_v)
    exp.package_changed("kernel-image", old_v, new_v)
    exp.package_changed("kernel-image-bzimage", old_v, new_v)
    exp.package_changed("kernel-module-uvesafb", old_v, new_v)

    run_sbom_diff_check(
        tmp_dir,
        sbom_data,
        "reference-sbom.spdx.json",
        "test-kernel-new-version.spdx.json",
        exp,
    )


def test_kernelconfig_n_to_m(tmp_dir: pathlib.Path, sbom_data: pathlib.Path) -> None:
    exp = ExpectedDiff()
    exp.same_expect_ignore_proprietary = True
    exp.kernel_config_added("CONFIG_AD525X_DPOT", "m")

    run_sbom_diff_check(
        tmp_dir,
        sbom_data,
        "reference-sbom.spdx.json",
        "test-kernelconfig-n-to-m.spdx.json",
        exp,
    )


def test_kernelconfig_n_to_y(tmp_dir: pathlib.Path, sbom_data: pathlib.Path) -> None:
    exp = ExpectedDiff()
    exp.same_expect_ignore_proprietary = True
    exp.kernel_config_added("CONFIG_AD525X_DPOT", "y")

    run_sbom_diff_check(
        tmp_dir,
        sbom_data,
        "reference-sbom.spdx.json",
        "test-kernelconfig-n-to-y.spdx.json",
        exp,
    )

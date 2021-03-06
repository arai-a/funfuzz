# coding=utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Allows detection of support for various command-line flags.
"""

from __future__ import absolute_import, print_function

import multiprocessing
import os
import random
import sys

from . import inspect_shell

if sys.version_info.major == 2:
    if os.name == "posix":
        import subprocess32 as subprocess  # pylint: disable=import-error
    from functools32 import lru_cache  # pylint: disable=import-error
else:
    import subprocess
    from functools import lru_cache  # pylint: disable=no-name-in-module


@lru_cache(maxsize=None)
def shell_supports_flag(shell_path, flag):
    """Returns whether a particular flag is supported by a shell.

    Args:
        shell_path (str): Path to the required shell.
        flag (str): Intended flag to test.

    Returns:
        bool: True if the flag is supported, i.e. does not cause the shell to throw an error, False otherwise.
    """
    dummy_parameters = ["-e", "42"]
    if "--gc-zeal=" in flag:
        # The js shell requires the double quotes in '--gc-zeal="0;0,1"',
        # but Python removes them unless we pass in shell=True
        try:
            subprocess.run(" ".join([shell_path, flag] + dummy_parameters),
                           shell=True, timeout=9, check=True).check_returncode()
            out = True
        except subprocess.CalledProcessError:
            out = False
    else:
        # This can be refactored when sps.captureStdout is gone
        out = inspect_shell.shellSupports(shell_path, [flag] + dummy_parameters)
    return out


def chance(i):
    """Returns a random boolean result based on an input probability.

    Args:
        i (float): Intended probability.

    Returns:
        bool: Result based on the input probability
    """
    return random.random() < i


def add_random_arch_flags(shell_path, input_list=False):
    """Returns a list with probably additional architecture-related flags added.

    Args:
        shell_path (str): Path to the required shell.
        input_list (list): List of flags to eventually be tested against a shell.

    Returns:
        list: List of flags to be tested, with probable architecture-related flags added.
    """
    if inspect_shell.queryBuildConfiguration(shell_path, "arm-simulator") and chance(.7):
        # m-c rev 165993:c450eb3abde4, see bug 965247
        input_list.append("--arm-sim-icache-checks")

    if shell_supports_flag(shell_path, "--enable-avx") and chance(.2):
        # m-c rev 223959:5e6e959f0043, see bug 1118235
        input_list.append("--enable-avx")
    elif shell_supports_flag(shell_path, "--no-avx") and chance(.2):
        # m-c rev 223959:5e6e959f0043, see bug 1118235
        input_list.append("--no-avx")

    # m-c rev 222786:bcacb5692ad9 is the earliest known working revision, so stop testing prior existence of flag

    if chance(.2):  # m-c rev 154600:526ba3ace37a, see bug 935791
        input_list.append("--no-sse" + ("3" if chance(.5) else "4"))

    return input_list


def add_random_ion_flags(shell_path, input_list=False):  # pylint: disable=too-complex,too-many-branches
    """Returns a list with probably additional IonMonkey flags added.

    The non-default options have a higher chance of being set, e.g. chance(.9)

    Args:
        shell_path (str): Path to the required shell.
        input_list (list): List of flags to eventually be tested against a shell.

    Returns:
        list: List of flags to be tested, with probable IonMonkey flags added.
    """
    if shell_supports_flag(shell_path, "--cache-ir-stubs=on") and chance(.2):
        # m-c rev 308931:1c5b92144e1e, see bug 1292659
        input_list.append("--cache-ir-stubs=" + ("on" if chance(.1) else "off"))
    if shell_supports_flag(shell_path, "--ion-aa=flow-sensitive") and chance(.2):
        # m-c rev 295435:c0c1d923c292, see bug 1255008
        input_list.append("--ion-aa=flow-" + ("" if chance(.9) else "in") + "sensitive")
    if shell_supports_flag(shell_path, "--ion-pgo=on") and chance(.2):
        # m-c rev 272274:b0a0ff5fa705, see bug 1209515
        input_list.append("--ion-pgo=" + ("on" if chance(.1) else "off"))
    if shell_supports_flag(shell_path, "--ion-sincos=on") and chance(.2):
        # m-c rev 262544:3dec2b935295, see bug 984018
        input_list.append("--ion-sincos=" + ("on" if chance(.5) else "off"))
    if shell_supports_flag(shell_path, "--ion-instruction-reordering=on") and chance(.2):
        # m-c rev 259672:59d2f2e62420, see bug 1195545
        input_list.append("--ion-instruction-reordering=" + ("on" if chance(.9) else "off"))
    if shell_supports_flag(shell_path, "--ion-shared-stubs=on") and chance(.2):
        # m-c rev 257573:3655d19ce241, see bug 1168756
        input_list.append("--ion-shared-stubs=" + ("on" if chance(.1) else "off"))
    if shell_supports_flag(shell_path, "--ion-regalloc=testbed") and chance(.2):
        # m-c rev 248962:47e92bae09fd, see bug 1170840
        input_list.append("--ion-regalloc=testbed")
    if shell_supports_flag(shell_path, "--non-writable-jitcode") and chance(.2):
        # m-c rev 248578:b46d6692fe50, see bug 977805
        input_list.append("--non-writable-jitcode")
    if (shell_supports_flag(shell_path, "--execute=setJitCompilerOption(\"ion.forceinlineCaches\",1)") and
            chance(.2)):
        # m-c rev 247709:ea9608e33abe, see bug 923717
        input_list.append("--execute=setJitCompilerOption(\"ion.forceinlineCaches\",1)")
    if shell_supports_flag(shell_path, "--ion-extra-checks") and chance(.2):
        # m-c rev 234228:cdf93416b39a, see bug 1139152
        input_list.append("--ion-extra-checks")

    # m-c rev 222786:bcacb5692ad9 is the earliest known working revision, so stop testing prior existence of flag

    # --ion-sink=on is still not ready to be fuzzed
    # if chance(.2):  # m-c rev 217242:9188c8b7962b, see bug 1093674
    #     input_list.append("--ion-sink=" + ("on" if chance(.1) else "off"))
    if chance(.2):  # m-c rev 198804:aa33f4725177, see bug 1039458
        input_list.append("--ion-loop-unrolling=" + ("on" if chance(.9) else "off"))
    if chance(.2):  # m-c rev 194672:b2a822934b97, see bug 992845
        input_list.append("--ion-scalar-replacement=" + ("on" if chance(.1) else "off"))
    if chance(.2):  # m-c rev 142933:f08e4a699011, see bug 894813
        input_list.append("--ion-check-range-analysis")
    # The stupid allocator isn't used by default and devs prefer not to have to fix fuzzbugs
    # if chance(.2):  # m-c rev 114120:7e97c5392d81, see bug 812945
        # input_list.append("--ion-regalloc=stupid")
    if chance(.2):  # m-c rev 106493:6688ede89a36, see bug 699883
        input_list.append("--ion-range-analysis=" + ("on" if chance(.1) else "off"))
    if chance(.2):  # m-c rev 106491:6c870a497ea4, see bug 699883
        input_list.append("--ion-edgecase-analysis=" + ("on" if chance(.1) else "off"))
    if chance(.2):  # m-c rev 106247:feac7727629c, see bug 755010
        input_list.append("--ion-limit-script-size=" + ("on" if chance(.1) else "off"))
    if chance(.2):  # m-c rev 105351:9fb668f0baca, see bug 700108
        input_list.append("--ion-osr=" + ("on" if chance(.1) else "off"))
    if chance(.2):  # m-c rev 105338:01ebfabf29e2, see bug 687901
        input_list.append("--ion-inlining=" + ("on" if chance(.1) else "off"))
    if chance(.7):  # m-c rev 105173:4ceb3e9961e4, see bug 683039
        input_list.append("--ion-eager")
    if chance(.2):  # m-c rev 104923:8db8eef79b8c, see bug 670816
        input_list.append("--ion-gvn=" + ("on" if chance(.1) else "off"))
    if chance(.2):  # m-c rev 104923:8db8eef79b8c, see bug 670816
        input_list.append("--ion-licm=" + ("on" if chance(.1) else "off"))

    return input_list


def add_random_wasm_flags(shell_path, input_list=False):
    """Returns a list with probably additional WebAssembly (wasm/asmjs) flags added.

    Args:
        shell_path (str): Path to the required shell.
        input_list (list): List of flags to eventually be tested against a shell.

    Returns:
        list: List of flags to be tested, with probable wasm flags added.
    """
    if shell_supports_flag(shell_path, "--test-wasm-await-tier2") and chance(.8):
        # m-c rev 387188:b1dc87a94262, see bug 1388785
        input_list.append("--test-wasm-await-tier2")
    if shell_supports_flag(shell_path, "--no-wasm-ion") and chance(.2):
        # m-c rev 375650:158b333a0a89, see bug 1277562
        input_list.append("--no-wasm-ion")
    if shell_supports_flag(shell_path, "--no-wasm-baseline") and chance(.2):
        # m-c rev 375639:9ea44ef0c07c, see bug 1277562
        input_list.append("--no-wasm-baseline")

    # m-c rev 222786:bcacb5692ad9 is the earliest known working revision, so stop testing prior existence of flag

    if chance(.7):  # m-c rev 124920:b3d85b68449d, see bug 840282
        input_list.append("--no-asmjs")

    return input_list


def random_flag_set(shell_path=False):  # pylint: disable=too-complex,too-many-branches,too-many-statements
    """Returns a random list of CLI flags appropriate for the given shell.

    Args:
        shell_path (str): Path to the required shell.

    Returns:
        list: List of flags to be tested.
    """
    args = []

    if shell_supports_flag(shell_path, "--fuzzing-safe"):  # This is always enabled if supported
        # m-c rev 135892:0a9314155404, see bug 885361
        args.append("--fuzzing-safe")

    # Add other groups of flags randomly
    if shell_supports_flag(shell_path, "--no-wasm"):
        # m-c rev 321230:e9b561d60697, see bug 1313180
        args = add_random_wasm_flags(shell_path, args)

    if shell_supports_flag(shell_path, "--no-sse3"):
        # m-c rev 154600:526ba3ace37a, see bug 935791
        args = add_random_arch_flags(shell_path, args)

    if shell_supports_flag(shell_path, "--ion") and chance(.7):
        # m-c rev 104923:8db8eef79b8c, see bug 670816
        args = add_random_ion_flags(shell_path, args)
    elif shell_supports_flag(shell_path, "--no-ion"):
        # m-c rev 106120:300ac3d58291, see bug 724751
        args.append("--no-ion")

    # Other flags
    if shell_supports_flag(shell_path, "--nursery-strings=on") and chance(.2):
        # m-c rev 406115:321c29f48508, see bug 903519
        args.append("--nursery-strings=" + ("on" if chance(.1) else "off"))

    if shell_supports_flag(shell_path, "--no-array-proto-values") and chance(.2):
        # m-c rev 403011:e1ca344ca6b5, see bug 1420101
        args.append("--no-array-proto-values")

    if shell_supports_flag(shell_path, "--spectre-mitigations=on") and chance(.2):
        # m-c rev 399868:a98f615965d7, see bug 1430053
        args.append("--spectre-mitigations=" + ("on" if chance(.9) else "off"))

    # m-c rev 380023:1b55231e6628, see bug 1206770
    if shell_supports_flag(shell_path, "--cpu-count=1"):
        if shell_supports_flag(shell_path, "--ion-offthread-compile=on") and chance(.7):
            # Focus on the reproducible cases
            # m-c rev 188900:9ab3b097f304, see bug 1020364
            args.append("--ion-offthread-compile=" + ("on" if chance(.1) else "off"))
        elif (chance(.5) and multiprocessing.cpu_count() > 1 and
              shell_supports_flag(shell_path, "--cpu-count=1")):
            # Adjusts default number of threads for offthread compilation (turned on by default)
            args.append("--cpu-count=%s" % random.randint(2, (multiprocessing.cpu_count() * 2)))

    # Stop testing --enable-streams until bug 1445854 is fixed.
    # if shell_supports_flag(shell_path, "--enable-streams") and chance(.2):
    #     # m-c rev 371894:64bbc26920aa, see bug 1272697
    #     args.append("--enable-streams")

    if shell_supports_flag(shell_path, "--no-unboxed-objects") and chance(.2):
        # m-c rev 244297:322487136b28, see bug 1162199
        args.append("--no-unboxed-objects")

    if shell_supports_flag(shell_path, "--no-cgc") and chance(.2):
        # m-c rev 226540:ade5e0300605, see bug 1126769
        args.append("--no-cgc")

    if shell_supports_flag(shell_path, '--gc-zeal="0;0,1"') and chance(.9):
        allocations_number = 999 if chance(.001) else random.randint(0, 500)  # 999 is for tests

        highest_gczeal = 18
        gczeal_value = highest_gczeal - 3  # 3 levels disabled below
        gczeal_a = final_value = 3 if chance(.001) else random.randint(0, gczeal_value)  # 3 is for tests

        gczeal_b = 4 if chance(.001) else random.randint(0, gczeal_value)  # 4 is for tests
        if gczeal_b >= 3:  # gczeal 3 does not exist, so repurpose it
            gczeal_b += 1
        if gczeal_b >= 5:  # gczeal 5 does not exist, so repurpose it
            gczeal_b += 1
        if gczeal_b >= 6:  # gczeal 6 does not exist, so repurpose it
            gczeal_b += 1

        if gczeal_a >= 3:  # gczeal 3 does not exist, so repurpose it
            gczeal_a += 1
            final_value = "%s;%s" % (gczeal_a, gczeal_b)
        if gczeal_a >= 5:  # gczeal 5 does not exist, so repurpose it
            gczeal_a += 1
            final_value = "%s;%s" % (gczeal_a, gczeal_b)
        if gczeal_a >= 6:  # gczeal 6 does not exist, so repurpose it
            gczeal_a += 1
            final_value = "%s;%s" % (gczeal_a, gczeal_b)

        # m-c rev 216625:03c6a758c9e8, see bug 1101602
        args.append('--gc-zeal="%s,%s"' % (final_value, allocations_number))

    if shell_supports_flag(shell_path, "--no-incremental-gc") and chance(.2):
        # m-c rev 211115:35025fd9e99b, see bug 958492
        args.append("--no-incremental-gc")

    if shell_supports_flag(shell_path, "--no-threads") and chance(.5):
        # m-c rev 195996:35038c3324ee, see bug 1031529
        args.append("--no-threads")

    if shell_supports_flag(shell_path, "--no-native-regexp") and chance(.2):
        # m-c rev 183413:43acd23f5a98, see bug 976446
        args.append("--no-native-regexp")

    if shell_supports_flag(shell_path, "--no-ggc") and chance(.2):
        # m-c rev 129273:3297733a2661, see bug 706885
        args.append("--no-ggc")

    # --baseline-eager landed after --no-baseline on the IonMonkey branch prior to landing on m-c.
    if shell_supports_flag(shell_path, "--baseline-eager"):
        if chance(.2):
            # m-c rev 127126:1c0489e5a302, see bug 818231
            args.append("--no-baseline")
        # elif is important, as we want to call --baseline-eager only if --no-baseline is not set.
        elif chance(.5):
            # m-c rev 127353:be125cabea26, see bug 843596
            args.append("--baseline-eager")

    if shell_supports_flag(shell_path, "--dump-bytecode") and chance(.05):
        # m-c rev 73054:b1923b866d6a, see bug 668095
        args.append("--dump-bytecode")

    return args


def basic_flag_sets(shell_path):
    """These flag combos are used w/the original flag sets when run through Lithium & autoBisect.

    Args:
        shell_path (str): Path to shell.

    Returns:
        list: Possible shell runtime flag combinations for fuzzing.
    """
    basic_flags = [
        # Parts of this flag permutation come from:
        # https://hg.mozilla.org/mozilla-central/file/c91249f41e37/js/src/tests/lib/tests.py#l13
        # compare_jit uses the following first flag set as the sole baseline when fuzzing
        ["--fuzzing-safe", "--no-threads", "--ion-eager"],
        ["--fuzzing-safe"],
        ["--fuzzing-safe", "--ion-offthread-compile=off", "--ion-eager"],
        ["--fuzzing-safe", "--ion-offthread-compile=off"],
        ["--fuzzing-safe", "--baseline-eager"],
        ["--fuzzing-safe", "--no-baseline", "--no-ion"],
    ]
    if shell_supports_flag(shell_path, "--non-writable-jitcode"):
        basic_flags.append(["--fuzzing-safe", "--no-threads", "--ion-eager",
                            "--non-writable-jitcode", "--ion-check-range-analysis",
                            "--ion-extra-checks", "--no-sse3"])
    if shell_supports_flag(shell_path, "--no-wasm"):
        basic_flags.append(["--fuzzing-safe", "--no-baseline", "--no-asmjs",
                            "--no-wasm", "--no-native-regexp"])
    if shell_supports_flag(shell_path, "--nursery-strings=on"):
        basic_flags.append(["--fuzzing-safe", "--ion-offthread-compile=off", "--ion-eager",
                            "--test-wasm-await-tier2", "--spectre-mitigations=on", "--nursery-strings=on"])
    return basic_flags

# SPDX-FileCopyrightText: 2025 Olivier Churlaud <olivier@churlaud.com>
# SPDX-FileCopyrightText: 2025 CNES
#
# SPDX-License-Identifier: MIT

from enum import IntEnum

class MALPY_ENCODING(IntEnum):
    BINARY = 1
    SPLITBINARY = 2
    XML = 3
    PICKLE = 50

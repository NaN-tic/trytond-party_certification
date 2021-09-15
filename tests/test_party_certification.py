# This file is part party_certification module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest


from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import suite as test_suite


class PartyCertificationTestCase(ModuleTestCase):
    'Test Party Certification module'
    module = 'party_certification'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            PartyCertificationTestCase))
    return suite

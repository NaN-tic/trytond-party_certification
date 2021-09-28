# This file is part party_certification module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import certification
from . import party


def register():
    Pool.register(
        certification.Cron,
        certification.Document,
        certification.DocumentType,
        certification.DocumentTypePartyType,
        certification.DocumentTypeSelectionChoice,
        certification.PartyType,
        certification.PartyTypeParty,
        certification.SelectionChoice,
        party.Party,
        module='party_certification', type_='model')
    Pool.register(
        module='party_certification', type_='wizard')
    Pool.register(
        module='party_certification', type_='report')

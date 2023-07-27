
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


class PartyCertificationTestCase(ModuleTestCase):
    'Test PartyCertification module'
    module = 'party_certification'

    @with_transaction()
    def test_party_certification(self):
        'Create category'
        pool = Pool()
        Party = pool.get('party.party')
        PartyType = pool.get('certification.party.type')
        DocumentType = pool.get('certification.document.type')
        DocumentTypePartyType = pool.get('certification.document.type-certification.party.type')
        Document = pool.get('certification.document')
        Date = pool.get('ir.date')

        today = Date().today()

        party1, = Party.create([{
                    'name': 'Party',
                    }])

        # Create document types
        document_type1, document_type2, document_type3 = DocumentType.create([{
                    'name': 'Document Type1',
                    'type': 'text',
                    }, {
                    'name': 'Document Type2',
                    'type': 'text',
                    }, {
                    'name': 'Document Type3',
                    'type': 'text',
                    }])
        # add document substitute
        document_type1.substitute = document_type3
        document_type1.save()

        # create party type and document party type
        party_type1, = PartyType.create([{
            'name': 'Party Type1',
            }])
        DocumentTypePartyType.create([{
                'party_type': party_type1,
                'document_type': document_type1,
                'required': True,
            }, {
                'party_type': party_type1,
                'document_type': document_type2,
                'required': True,
            }])

        # add party_type in the party
        party1.party_types = [party_type1]
        party1.save()

        Party.generate_party_documents([party1])

        self.assertEqual(len(party1.documents), 3)
        self.assertEqual(party1.valid_documents, False)

        document2, document3, document1 = party1.documents

        document2.expiration_date = today
        document2.text = 'Test'
        document2.save()
        Document.approve([document2])
        self.assertEqual(party1.valid_documents, False)

        # document3.expiration_date = today
        document3.text = 'Test'
        document3.save()
        Document.approve([document3])
        self.assertEqual(party1.valid_documents, True)

del ModuleTestCase

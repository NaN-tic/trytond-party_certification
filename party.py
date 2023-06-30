from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.model import ModelView
from trytond.i18n import gettext
from trytond.exceptions import UserError


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'
    party_types = fields.Many2Many(
        'certification.party.type-party.party',
        'party', 'party_type', "Party Type")
    documents = fields.One2Many('certification.document', 'party', 'Documents')
    valid_documents = fields.Function(
        fields.Boolean("Valid Documents"), 'get_valid_documents')
    certification_not_available = fields.Boolean('Not Available')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({
            'generate_party_documents': {},
            })

    def get_valid_documents(self, name):
        pool = Pool()
        PartyTypeParty = pool.get('certification.party.type-party.party')

        data = PartyTypeParty.search(['party', '=', self.id])
        for type in data:
            if not type.valid:
                break
        else:
            return True

    @classmethod
    @ModelView.button
    def generate_party_documents(cls, parties):
        pool = Pool()
        Document = pool.get('certification.document')

        to_delete = []
        documents = []
        for party in parties:
            current_types = [
                d.document_type for d in party.documents
                if d.state in ['waiting-approval', 'approved']
                ]
            expected_types = set()
            for party_type in party.party_types:
                for document_type in party_type.document_types:
                    if party.certification_not_available:
                        doc_type = document_type.document_type.substitute
                    else:
                        doc_type = document_type.document_type
                    if not doc_type:
                        raise UserError(
                            gettext('party_certification.msg_missign_document_type',
                            document_type=document_type.rec_name,
                            party=party.rec_name))
                    expected_types.add(doc_type)

            for document in party.documents:
                if (not document.text
                        and not document.attachment
                        and not document.selection
                        and document.document_type not in expected_types):
                    to_delete.append(document)

            for document_type in expected_types:
                if document_type not in current_types:
                    document = Document()
                    document.document_type = document_type
                    document.party = party
                    document.state = 'waiting-approval'
                    document.type = document_type.type
                    documents.append(document)
                    # party.documents += (document,)

        Document.delete(to_delete)
        Document.save(documents)

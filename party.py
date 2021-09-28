from trytond.model import fields
from trytond.pool import Pool, PoolMeta


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'
    party_types = fields.Many2Many(
        'certification.party.type-party.party',
        'party', 'party_type', "Party Type")
    documents = fields.One2Many('certification.document', 'party', 'Documents')
    valid_documents = fields.Function(
        fields.Boolean("Valid Documents"), 'get_valid_documents')

    def get_valid_documents(self, name):
        pool = Pool()
        partyTypeParty = pool.get('certification.party.type-party.party')

        data = partyTypeParty.search(['party', '=', self.id])
        for type in data:
            if not type.valid:
                break
        else:
            return True

    @fields.depends('party_types', 'documents')
    def on_change_party_types(self):
        pool = Pool()
        Document = pool.get('certification.document')
        current_types = [d.document_type for d in self.documents]
        for party_type in self.party_types:
            for document_type in party_type.document_types:
                if document_type.document_type not in current_types:
                    document = Document()
                    document.document_type = document_type.document_type.id
                    document.party = self.id
                    self.documents += (document,)

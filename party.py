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

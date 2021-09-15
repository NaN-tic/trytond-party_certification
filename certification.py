from trytond.model import (
    ModelSQL, ModelView, fields, DeactivableMixin, Workflow)
from trytond.pool import Pool, PoolMeta
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond.pyson import Eval, Bool, If


class Document(Workflow, ModelSQL, ModelView):
    "Certification Document"
    __name__ = 'certification.document'
    party = fields.Many2One('party.party', "Party")
    document_type = fields.Many2One(
        'certification.document.type', "Document Type")
    type = fields.Function(fields.Char('Type'), 'get_type')
    text = fields.Char('Text', states={
        'invisible': Eval('type') != 'text'
        }, depends=['type', 'document_type'])
    attachment = fields.Binary('Attachment', states={
        'invisible': Eval('type') != 'attachment'
        }, depends=['type', 'document_type'])
    selection = fields.Many2One('certification.selection.choice', 'Selection',
        domain=[(
            'id', 'in', Eval('choices')
        )],
        states={
            'invisible': Eval('type') != 'selection'
        }, depends=['type', 'choices', 'document_type'])
    choices = fields.Function(fields.Many2Many(
        'certification.selection.choice', None, None, 'Choices'), 'get_choices')
    from_date = fields.Date('From Date', required=True,
        domain=[
            If(Bool(Eval('from_date')) & Bool(Eval('to_date')),
                ('from_date', '<=', Eval('to_date')), ())],
        states={
            'readonly': Eval('state') != 'waiting-approval',
        }, depends=['state', 'to_date', 'from_date'])
    to_date = fields.Date('To Date', required=True,
        domain=[
            If(Bool(Eval('from_date')) & Bool(Eval('to_date')),
                ('from_date', '<=', Eval('to_date')), ())],
        states={
            'readonly': Eval('state') != 'waiting-approval',
        }, depends=['state', 'to_date', 'from_date'])
    state = fields.Selection([
            ('waiting-approval', 'Waiting Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('expirated', 'Expirated'),
            ], 'State', readonly=True, required=True)

    @classmethod
    def __setup__(cls):
        super(Document, cls).__setup__()
        cls._transitions |= {
            ('waiting-approval', 'approved'),
            ('waiting-approval', 'rejected'),
            ('waiting-approval', 'expirated'),
            }
        cls._buttons.update({
            'approve': {
                'invisible': Eval('state') != 'waiting-approval',
                'depends': ['state'],
                },
            'reject': {
                'invisible': Eval('state') != 'waiting-approval',
                'depends': ['state'],
                },
            'expire': {
                'invisible': Eval('state') != 'waiting-approval',
                'depends': ['state'],
                },
            })

    @staticmethod
    def default_state():
        return 'waiting-approval'

    @classmethod
    @ModelView.button
    @Workflow.transition('approved')
    def approve(cls, documents):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('rejected')
    def reject(cls, documents):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('expirated')
    def expire(cls, documents):
        pass

    def get_type(self, name):
        if self.document_type:
            return self.document_type.type

    def get_choices(self, name):
        print(self.document_type)
        print(self.document_type.selection_choices)
        if self.document_type and self.document_type.selection_choices:
            print([c.id for c in self.document_type.selection_choices])
            return [c.id for c in self.document_type.selection_choices]


class DocumentType(ModelSQL, ModelView):
    "Certification Document Type"
    __name__ = 'certification.document.type'
    name = fields.Char('Name', required=True)
    type = fields.Selection([
        ('text', 'Text'),
        ('selection', 'Selection'),
        ('attachment', 'Attachment'),
        ], 'Type', required=True)
    selection_choices = fields.Many2Many(
        'certification.type-certification.selection.choice',
        'document_type', 'selection_choice', 'Selection Choices',
        states={
            'invisible': Eval('type') != 'selection',
            'required': Eval('type') == 'selection'
        },
        depends=['type'],)


class DocumentTypePartyType(ModelSQL, ModelView):
    "Document Type - Party Type"
    __name__ = 'certification.document.type-certification.party.type'
    document_type = fields.Many2One(
        'certification.document.type', 'Document Type')
    required = fields.Boolean('Required')
    expiration_date = fields.Boolean('Expiration Date')
    party_type = fields.Many2One('certification.party.type', 'Party Type')


class PartyType(ModelSQL, ModelView):
    "Certification Party Type"
    __name__ = 'certification.party.type'
    name = fields.Char('Name', required=True)
    document_types = fields.One2Many(
        'certification.document.type-certification.party.type',
        'party_type', 'Document Types')


class SelectionChoice(DeactivableMixin, ModelSQL, ModelView):
    "Certification Selection Choice"
    __name__ = 'certification.selection.choice'
    name = fields.Char('Name', required=True)


class DocumentTypeSelectionChoice(ModelSQL, ModelView):
    "Document Type - Selection Choice"
    __name__ = 'certification.type-certification.selection.choice'
    document_type = fields.Many2One(
        'certification.document.type', 'Document Type')
    selection_choice = fields.Many2One(
        'certification.selection.choice', "Selection Choice")


class PartyTypeParty(ModelSQL, ModelView):
    "Party Type - Party"
    __name__ = 'certification.party.type-party.party'
    party_type = fields.Many2One(
        'certification.party.type', 'Party Type')
    party = fields.Many2One(
        'party.party', "Party")
    valid = fields.Function(fields.Boolean('Valid'), 'is_valid')

    def is_valid(self, name):
        required_documents = set()
        for line in self.party_type.document_types:
            if line.required:
                required_documents.add(line.document_type.id)

        for document in self.party.documents:
            if (document.state == 'approved' and
                    document.document_type.id in required_documents):
                required_documents.remove(document.document_type.id)

        if not required_documents:
            return True
        return False

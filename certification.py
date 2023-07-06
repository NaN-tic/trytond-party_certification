from trytond.model import (
    ModelSQL, ModelView, fields, DeactivableMixin, Workflow)
from trytond.pyson import Eval, Bool, And
from trytond.pool import Pool, PoolMeta
from trytond.exceptions import UserError
from trytond.i18n import gettext


class Document(Workflow, ModelSQL, ModelView):
    "Certification Document"
    __name__ = 'certification.document'
    party = fields.Many2One('party.party', "Party", required=True,
        states={
            'readonly': Eval('state') != 'waiting-approval',
        }, depends=['state'])
    document_type = fields.Many2One(
        'certification.document.type', "Document Type", required=True,
        states={
            'readonly': Eval('state') != 'waiting-approval',
        }, depends=['state'])
    type = fields.Function(fields.Char('Type'),
        'on_change_with_type')
    text = fields.Char('Text', states={
        'readonly': Eval('state') != 'waiting-approval',
        'invisible': Eval('type') != 'text',
        'required': And(
                Eval('state') != 'waiting-approval',
                Eval('type') == 'text')
        }, depends=['type'])
    attachment = fields.Binary('Attachment', states={
        'readonly': Eval('state') != 'waiting-approval',
        'invisible': Eval('type') != 'attachment',
        'required': And(
                Eval('state') != 'waiting-approval',
                Eval('type') == 'attachment')
        }, depends=['type'])
    selection = fields.Many2One('certification.selection.choice', 'Selection',
        domain=[
            ('id', 'in', Eval('choices')),
        ], states={
            'readonly': Eval('state') != 'waiting-approval',
            'invisible': Eval('type') != 'selection',
            'required': And(
                Eval('state') != 'waiting-approval',
                Eval('type') == 'selection')
        }, depends=['type', 'choices'])
    choices = fields.Function(fields.Many2Many(
        'certification.selection.choice', None, None, 'Choices'),
        'on_change_with_choices')
    expiration_date = fields.Date('Expiration Date',
        states={
            'readonly': Eval('state') != 'waiting-approval',
            'required': And(
                Eval('state') != 'waiting-approval',
                Bool(Eval('required_expiration_date'))),
        }, depends=['state', 'required_expiration_date'])
    state = fields.Selection([
            ('waiting-approval', 'Waiting Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('expired', 'Expired'),
            ], 'State', readonly=True, required=True)
    required_expiration_date = fields.Function(
        fields.Boolean('Required Expiration Date'),
        'on_change_with_required_expiration_date')

    @classmethod
    def __setup__(cls):
        super(Document, cls).__setup__()
        cls._transitions |= {
            ('waiting-approval', 'approved'),
            ('waiting-approval', 'rejected'),
            ('waiting-approval', 'expired'),
            ('approved', 'expired'),
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

    @fields.depends('party', 'document_type', '_parent_party.party_types')
    def on_change_with_required_expiration_date(self, name=None):
        if not self.party or not self.document_type:
            return
        for pt in self.party.party_types:
            for dt in pt.document_types:
                if (dt.document_type == self.document_type
                        and dt.expiration_date):
                    return True

    @staticmethod
    def default_state():
        return 'waiting-approval'

    @classmethod
    @ModelView.button
    @Workflow.transition('approved')
    def approve(cls, documents):
        pool = Pool()
        today = pool.get('ir.date').today()
        for document in documents:
            if document.expiration_date:
                if document.expiration_date < today:
                    raise UserError(gettext(
                        'party_certification.msg_expired_document',
                        document=document.rec_name))

    @classmethod
    @ModelView.button
    @Workflow.transition('rejected')
    def reject(cls, documents):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('expired')
    def expire(cls, documents):
        pass

    @fields.depends('document_type')
    def on_change_with_type(self, name=None):
        if self.document_type:
            return self.document_type.type

    @fields.depends('document_type')
    def on_change_with_choices(self, name=None):
        if self.document_type and self.document_type.selection_choices:
            return [c.id for c in self.document_type.selection_choices]
        return[]

    @classmethod
    def check_expiration_date_cron(cls):
        pool = Pool()
        today = pool.get('ir.date').today()
        records = cls.search([
            ('expiration_date', '<', today),
            ('state', 'in', ['waiting-approval', 'approved'])
        ])
        cls.expire(records)


class DocumentType(ModelSQL, ModelView):
    "Certification Document Type"
    __name__ = 'certification.document.type'
    name = fields.Char('Name', required=True, translate=True)
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
        depends=['type'])
    substitute = fields.Many2One('certification.document.type', 'Substitute',
        domain=[
            ('id', '!=', Eval('id', -1)),
        ], depends=['id'])


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
    name = fields.Char('Name', required=True, translate=True)
    document_types = fields.One2Many(
        'certification.document.type-certification.party.type',
        'party_type', 'Document Types')


class SelectionChoice(DeactivableMixin, ModelSQL, ModelView):
    "Certification Selection Choice"
    __name__ = 'certification.selection.choice'
    name = fields.Char('Name', required=True, translate=True)


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
        pool = Pool()
        Date = pool.get('ir.date')

        today = Date.today()

        required_documents = set()
        required_substitute = {}
        for document_type in self.party_type.document_types:
            if document_type.required:
                document_type_id = document_type.document_type.id
                required_documents.add(document_type_id)
                if document_type.document_type.substitute:
                    sub_doc_type_id = document_type.document_type.substitute.id
                    required_substitute[sub_doc_type_id] = document_type_id

        for document in self.party.documents:
            document_type_id = document.document_type.id
            if (document.state == 'approved' and
                    document_type_id in required_documents):
                # in case has expiration_date, not valid
                if document.expiration_date and document.expiration_date < today:
                    continue
                required_documents.remove(document_type_id)

            # remove in case has approved document is required and has substitute
            document_type_parent_id = required_substitute.get(document_type_id)
            if (document.state == 'approved' and
                    document_type_parent_id in required_documents):
                # in case has expiration_date, not valid
                if document.expiration_date and document.expiration_date < today:
                    continue
                required_documents.remove(document_type_parent_id)

        if not required_documents:
            return True
        return False


class Cron(metaclass=PoolMeta):
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super(Cron, cls).__setup__()
        cls.method.selection.append(
            ('certification.document|check_expiration_date_cron',
            "Check Expiration Date"),
            )

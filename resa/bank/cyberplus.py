# -*- coding: utf-8 -*-
import os, os.path, popen2
from decimal import Decimal as dec

from django.utils.translation import ugettext_lazy as _
from django.utils import translation
from django.contrib.auth.models import User

from bank import Bank
from resarmll import settings
from resarmll.resa.models import TransactionId
from resarmll.resa.orders import Order
from resarmll.utils.mail import send_email, send_admins
from resarmll.compta.models import PaymentMethod
from resarmll.compta.models import SupplierAccount

class CyberPlus(Bank):
    def __init__(self, req):
        super(CyberPlus, self).__init__(req, True)

    def get_paiement_method(self):
        try:
            method = PaymentMethod.objects.filter(code=settings.COMPTA_METHOD_CODE_BANK)[0]
        except:
            method = None
        return method

    def get_supplier_account(self):
        try:
            account = SupplierAccount.objects.filter(label__startswith='CyberPlus')[0]
        except:
            account = None
        return account

    def fix_lang(self, lang):
        lang =lang[:2]
        if lang == 'es':
            lang = 'sp'
        return lang

    def get_transactionid(self):
        t = TransactionId()
        t.save()
        return t.id

    def process(self, cmd):
        nwd = "%s/cyberplus/" % (os.path.dirname(__file__))
        cmd = "cd %s && ./%s" % (nwd, cmd)
        stdout, stdin, stderr = popen2.popen3(cmd)
        stdin.close()
        stderr.close()
        lines = stdout.readlines()
        stdout.close()
        return "\n".join(lines).strip()

    def form(self, order, user, lang, ip_addr, url=None):
        args = []
        args.append('pathfile=pathfile')
        args.append('language=%s' % self.fix_lang(lang))
        args.append('customer_id=%d' % (user.id))
        args.append('customer_email=%s' % (user.email))
        args.append('customer_ip_address=%s' % (ip_addr))
        for k,v in settings.CYBERPLUS_SETTINGS.iteritems():
            if url and k.endswith('_url'):
                if k == 'automatic_response_url':
                    args.append('%s=%s%s' % (k, url.replace('https://', 'http://'), v))
                else:
                    args.append('%s=%s%s' % (k, url, v))
            else:
                args.append('%s=%s' % (k, v))
        args.append('order_id=%d' % (order.id))
        args.append('amount=%d' % (order.totalamount()*100))
        args.append('transaction_id=%d' % (self.get_transactionid()))
        args.append('caddie=Com.%d' % (order.id))

        cmd = 'request ' + " ".join(args)
        error = True
        content = None
        result = self.process(cmd)
        datas = result.split('!')
        if len(datas)>=4:
            error = datas[1] != '0'
            code = datas[2]
            content = "!".join(datas[3:-1])
        # ugly html
        content = '<!-- begin: ugly html generated by CyberPlus !-->' + content + '<!-- end: ugly html generated by CyberPlus !-->'
        return error, code, content

    def getreturndatas(self):
        args = []
        args.append('pathfile=pathfile')
        args.append('message=%s' % (self.datas['DATA']))
        cmd = 'response ' + " ".join(args)
        error = True
        params = []
        result = self.process(cmd)
        datas = result.split('!')
        if len(datas)>=4:
            error = datas[1] != '0'
            code = datas[2]
            params = datas[3:-1]
        attr = {}
        if params:
            attr['merchant_id'] = params[0]
            attr['merchant_country'] = params[1]
            attr['amount'] = params[2]
            attr['transaction_id'] = params[3]
            attr['payment_means'] = params[4]
            attr['transmission_date'] = params[5]
            attr['payment_time'] = params[6]
            attr['payment_date'] = params[7]
            attr['response_code'] = params[8]
            attr['payment_certificate'] = params[9]
            attr['authorisation_id'] = params[10]
            attr['currency_code'] = params[11]
            attr['card_number'] = params[12]
            attr['cvv_flag'] = params[13]
            attr['cvv_response_code'] = params[14]
            attr['bank_response_code'] = params[15]
            attr['complementary_code'] = params[16]
            attr['complementary_info'] = params[17]
            attr['return_context'] = params[18]
            attr['caddie'] = params[19]
            attr['receipt_complement'] = params[20]
            attr['merchant_language'] = params[21]
            attr['language'] = params[22]
            attr['customer_id'] = params[23]
            attr['order_id'] = params[24]
            attr['customer_email'] = params[25]
            attr['customer_ip_address'] = params[26]
            attr['capture_day'] = params[27]
            attr['capture_mode'] = params[28]
        return error, code, attr

    def getreturn(self):
        error, code, params = self.getreturndatas()
        rejected = accepted = order_id = None
        if params:
            canceled = params['bank_response_code'] == ''
            rejected = params['bank_response_code'] == '05'
            accepted = params['bank_response_code'] == '00'
            order_id = params['order_id']
        return error, code, canceled, rejected, accepted, order_id

    def process_order(self):
        error, code, params = self.getreturndatas()
        if error or not params:
            self.add_error(_(u"Error while receiving data from the bank: [%s]") % (code))
        else:
            try:
                order = Order.objects.get(id=int(params['order_id']))
            except:
                order = None
            if not order:
                self.add_error(_(u"Unable to find order with id: #%d") % (order.id))
            elif order.payment_date != None:
                self.add_error(_(u"Order with id: #%d has already been paid") % (order.id))
            else:
                if params['bank_response_code'] != '00':
                    self.add_error(_(u"Wrong parameter '%(arg1)s': [%(arg2)s] instead of [%(arg3)s]") %
                        {'arg1': 'bank_response_code', 'arg2': params['bank_response_code'], 'arg3': '00'})
                if params['merchant_id'] != settings.CYBERPLUS_SETTINGS['merchant_id']:
                    self.add_error(_(u"Wrong parameter '%(arg1)s': [%(arg2)s] instead of [%(arg3)s]") %
                        {'arg1': 'merchant_id', 'arg2': params['merchant_id'], 'arg3': settings.CYBERPLUS_SETTINGS['merchant_id']})
                if params['currency_code'] != settings.CYBERPLUS_SETTINGS['currency_code']:
                    self.add_error(_(u"Wrong parameter '%(arg1)s': [%(arg2)s] instead of [%(arg3)s]") %
                        {'arg1': 'currency_code', 'arg2': params['currency_code'], 'arg3': settings.CYBERPLUS_SETTINGS['currency_code']})
                amount = dec(params['amount']) / 100
                if amount != order.totalamount():
                    self.add_error(_(u"Wrong parameter '%(arg1)s': [%(arg2)s] instead of [%(arg3)s]") %
                        {'arg1': 'amount', 'arg2': amount, 'arg3': order.totalamount()})

                if not self.has_errors():
                    try:
                        user = User.objects.get(id=order.user_id)
                    except:
                        user = None
                    if not user:
                        self.add_error(_(u"Cannot find user associated to order no: #%d") % (order.id))
                    else:
                        fee = dec(str(settings.COMPTA_BANK_FEE))
                        # mark order as paid
                        self.order_paid(order, fee, user, 'ref:'+params['transaction_id'])

                        # mail info to admins
                        send_admins(
                            "CYBERPLUS OK - [order=%d] [amount=%.2f] [user=%s] [email=%s]" %
                                (order.id, order.totalamount(), user.id, user.email),
                            "resa/payment_ok_cyberplus_admin_email.txt",
                            {'order_id': order.id, 'amount': order.totalamount(),
                            'env': self.env_datas(), 'dump': params})

                        # switch language before sending mail
                        translation.activate(user.get_profile().language)
                        # mail info to user
                        send_email([user.email], _(u"Bank payment - order no #%d") % order.id,
                            "resa/payment_cyberplus_email.txt",
                            {'order_id': order.id, 'amount': order.totalamount()})

        if self.has_errors():
            send_admins(
                "CYBERPLUS FAIL",
                "resa/payment_fail_admin_email.txt",
                {'errors': "\n".join(self.errors),
                'env': self.env_datas(), 'dump': params})

# https://github.com/saleor/saleor
# Uses PostgreSQL
# Found in Tang et al. Ad Hoc Transactions in Web Applications: The Good, the Bad, and the Ugly

# Contextual note: select_for_update is used to lock rows until the end of the transaction. 
# Django docs: https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update 

import numpy as np
import datetime

class Voucher: 
    def __init__(self):
        self.is_voucher_usage_increased: bool = np.random.binomial(1, 0.5)
        self.usage_limit: int = int(np.random.normal(5, 1))
        self.apply_once_per_customer: bool = np.random.binomial(1, 0.5)
        self.single_use: bool = np.random.binomial(1, 0.5)
        self.exists: bool = np.random.binomial(1, 0.5)

class Code:
    def __init__(self):
        voucher_ids = list(range(100))
        self.used: int = np.random.choice(range(10))
        self.is_active: bool = np.random.binomial(1, 0.5)
        self.voucher_id: int = np.random.choice(voucher_ids)

class Payment:
    def __init__(self):
        self.id: int = np.random.choice(range(100))
        self.to_confirm: bool = np.random.binomial(1, 0.5)
        self.is_active: bool = np.random.binomial(1, 0.5)
        self.can_refund: bool = np.random.binomial(1, 0.5)
        self.can_void: bool = np.random.binomial(1, 0.5)

class Checkout:
    def __init__(self):
        self.is_voucher_usage_increased: bool = np.random.binomial(1, 0.5)
        self.completing_started_at: datetime.datetime = np.random.choice([datetime.datetime.now(), None])
        self.exists: bool = np.random.binomial(1, 0.9)

# Transaction 1
def saleor_checkout_voucher_code_generator(voucher_code: int) -> list[list[str]]:
    """
    Purpose: Coordinate concurrent checkout.
    saleor/checkout/complete_checkout.py#complete_checkout(with voucher code usage)
    
    Focusing on _increase_voucher_code_usage_value
    https://github.com/saleor/saleor/blob/c0423c3cd4968b287d71896d086e03483ac196d1/saleor/checkout/complete_checkout.py#L1498
    PSEUDOCODE: 
    In: checkout_info
    TRANSACTION START
    ** get_voucher_for_checkout part
    if checkout_info.voucher_code is not None:
        code = Select * from voucher_codes where code=checkout_info.voucher_code and is_active=True
        if code DNE: TRANSACTION COMMIT
        if checkout_info.is_voucher_usage_increased:
            voucher = Select * from vouchers where id=code.voucher_id LIMIT 1
        else:
            voucher = Select * from vouchers where id=code.voucher_id and active_in_channel=checkout_info.channel_id LIMIT 1????
    
    if not voucher: TRANSACTION COMMIT

    if voucher.usage_limit is not None and with_lock:
        code = Select * from voucher_codes where code=checkout_info.voucher_code FOR UPDATE

    ** _increase_checkout_voucher_usage part
    if checkout.is_voucher_usage_increased: TRANSACTION COMMIT
    if voucher.usage_limit: # increase_voucher_code_usage_value
        from voucher_codes set usage=usage+1 where code=checkout_info.voucher_code
    if voucher.apply_once_per_customer and increase_voucher_customer_usage: # add_voucher_usage_by_customer
        if not customer_email: TRANSACTION ABORT
        created = get_or_create from voucher_customer where voucher_id=code and customer_email=customer_email
        if not created: TRANSACTION ABORT
    if voucher.single_use: # deactivate_voucher_code
        from voucher_codes set is_active=False where code=checkout_info.voucher_code

    TRANSACTION COMMIT
    """
    txn = []

    with_lock = True
    
    if voucher_code is not None:
        # Get code using voucher_code
        code = Code()
        txn.append(f"r-{code.voucher_id}")
        if code.voucher_id == 0: # if the code DNE
            return txn

        # Get voucher using code.voucher_id
        voucher = Voucher()

        if voucher.is_voucher_usage_increased:
            voucher_invalid = np.random.binomial(1, 0.5) # Chance of voucher being invalid after fully being used (deactivated)
            if voucher_invalid:
                txn.append(f"r-{voucher_code}")
                return txn
        txn.append(f"r-{voucher_code}")
        
        if voucher.usage_limit > 0 and with_lock:
            txn.append(f"r-{code.voucher_id}")
        
    # Increase voucher usage
    if voucher.usage_limit:
        txn.append(f"w-{code.used + 1}")
    if voucher.apply_once_per_customer:
        txn.append(f"w-{voucher_code}")
    if voucher.single_use:
        txn.append(f"w-{False}")
    return txn

def saleor_checkout_voucher_code_sim():
    """
    Example output:

    ['r-76', 'r-32', 'r-76', 'w-6', 'w-32', 'w-False']
    ['r-22', 'r-33']
    ['r-23', 'r-15', 'r-23', 'w-4']
    ['r-53', 'r-43']
    ['r-31', 'r-47', 'r-31', 'w-4']
    ['r-34', 'r-29']
    ['r-58', 'r-83', 'r-58', 'w-6', 'w-False']
    ['r-62', 'r-27', 'r-62', 'w-5', 'w-27']
    ['r-42', 'r-35', 'r-42', 'w-10', 'w-35']
    ['r-21', 'r-96', 'r-21', 'w-8']
    """
    voucher_codes = list(range(100))
    num_txn = 10
    for _ in range(num_txn):
        voucher_code = np.random.choice(voucher_codes)
        result = saleor_checkout_voucher_code_generator(voucher_code)
        print(result)

def saleor_payment_authorize():
    """
    Transaction 2
    Purpose: Coordinate concurrent payment processing.
    saleor/payment/gateway.py#authorize
    """

def saleor_payment_order():
    """
    Transaction 3
    Purpose: Coordinate concurrent payment processing.
    saleor/graphql/order/mutations/orders.py#OrderCapture
    """

def saleor_payment_refund():
    """
    Transaction 4
    Purpose: Coordinate concurrent payment processing.
    saleor/order/actions.py#create_refund_fulfillment
    """

def saleor_checkout_void_payment():
    """
    Transaction 5
    Purpose: Coordinate concurrent payment processing.
    saleor/checkout/complete_checkout.py#complete_checkout(with payment to void)
    (complete_checkout_with_payment) https://github.com/saleor/saleor/blob/27eed6e93f79a73b81cf97465ba8552b66d31c40/saleor/checkout/complete_checkout.py#L1781
    (_complete_checkout_fail_handler) https://github.com/saleor/saleor/blob/27eed6e93f79a73b81cf97465ba8552b66d31c40/saleor/checkout/complete_checkout.py#L1867
    (gateway.paymend_refund_or_void) https://github.com/saleor/saleor/blob/2ee9490104e6b256899d90adcde9f7bdfbcecfe1/saleor/payment/gateway.py#L535
    """

def saleor_checkout_confirm_payment():
    """
    Transaction 6
    Purpose: Coordinate concurrent checkout.
    saleor/checkout/complete_checkout.py#complete_checkout(with payment to confirm)
    https://github.com/saleor/saleor/blob/2ee9490104e6b256899d90adcde9f7bdfbcecfe1/saleor/payment/gateway.py#L452
    """

def saleor_cancel_fulfillment():
    """
    Transaction 7
    Purpose: Coordinate concurrent fulfillment cancel.
    saleor/graphql/order/mutations/fulfillments.py#FulfillmentCancel
    """

def saleor_fulfill_order():
    """
    Transaction 8
    Purpose: Coordinate concurrent fulfillment.
    saleor/graphql/order/mutations/fulfillments.py#OrderFulfill
    """

def saleor_get_payment_adyen():
    """
    Transaction 9
    Purpose: Coordinate concurrent payment processing.
    saleor/payment/gateways/adyen/webhooks.py#get_payment
    """

def saleor_get_checkout_adyen():
    """
    Transaction 10
    Purpose: Coordinate concurrent order processing.
    saleor/payment/gateways/adyen/webhooks.py#get_checkout
    """

def saleor_get_payment_stripe():
    """
    Transaction 11
    Purpose: Coordinate concurrent payment processing.
    saleor/payment/gateways/stripe/webhooks.py#get_payment
    """

def saleor_get_checkout_stripe():
    """
    Transaction 12
    Purpose: Coordinate concurrent order processing.
    saleor/payment/gateways/stripe/webhooks.py#get_checkout
    """

def saleor_get_delete_categories():
    """
    Transaction 13
    Purpose: Coordinate concurrent categories updating.
    saleor/product/utils/__init__.py#delete_categories
    """

def saleor_get_order_line_update():
    """
    Transaction 14
    Purpose: Coordinate concurrent order updating.
    saleor/warehouse/management.py#OrderLineUpdate
    """

def saleor_get_order_line_create():
    """
    Transaction 15
    Purpose: Coordinate concurrent order updating.
    saleor/graphql/order/mutations/orders.py#OrderLineCreate
    """

def saleor_checkout_payment_process_generator(checkout_pk: int) -> list[list[str]]:
    """
    Transaction 16
    Purpose: Coordinate concurrent checkout.
    saleor/checkout/complete_checkout.py#complete_checkout(with payment to process)
    
    Focusing on payment portion of complete_checkout_with_payment
    This includes _process_payment and _complete_checkout_fail_handler
    https://github.com/saleor/saleor/blob/c0423c3cd4968b287d71896d086e03483ac196d1/saleor/checkout/complete_checkout.py#L1754
    PSEUDOCODE:
    In: checkout_pk, payment 
    TRANSACTION START
    checkout = Select * from Checkout where pk=checkout_pk FOR UPDATE LIMIT 1
    if not checkout: 
        order = Select * from Order where checkout_id=checkout_pk
        TRANSACTION COMMIT

    payment = Select * from Payment where id=payment_id FOR UPDATE
    
    ** _process_payment part (note this is not exactly how the code is laid out but logically is the same
    ie. there's some redundant code across helper fns that I consolidated)
    try:
        if payment.to_confirm: (default is False)
            txn = Select * from Transactions where kind=ACTION_TO_CONFIRM LIMIT 1 (get_action_to_confirm)
        response, error = _fetch_gateway_response
        if response: 
            update_payment (save) –> write
        if gateway_response.transaction_already_processed:
            txn = Select * from Transactions where ... DESCENDING LIMIT 1 (get_already_processed_transaction)
        else: 
            txn = "create_transaction" (not r/w)
    except error:
        _complete_checkout_fail_handler
    
    ** _complete_checkout_fail_handler part
    refresh_from_db(payment)
    if not payment_is_active:
        if checkout.completing_started_at is not None:
            append to update_fields
        
        if voucher: 
            if checkout_update_fields is None:
                is_voucher_usage_increased=False (save) –> write
            if voucher_code:
                if voucher.usage_limit: # decrease_voucher_code_usage_value
                    from voucher_codes set usage=usage-1 where code=checkout_info.voucher_code
                if voucher.single_use: # deactivate_voucher_code
                    from voucher_codes set is_active=False where code=checkout_info.voucher_code
                if user_email:
                    voucher_customer = Select * from voucher_customer where voucher_id=code and customer_email=user_email
                    if voucher_customer: delete –> write
        if update_fields:
            checkout (save) –> write
        
        if payment: # called with transaction_id = None
            if payment.can_refund():
                txn = select * from transactions where kind=kind DESC LIMIT 1
                if txn is None: TRANSACTION ABORT
                select * from transactions where payment_id=payment_id and kind=kind
                TRANSACTION COMMIT
            elif payment.can_void():
                txn = select * from transactions where kind=kind DESC LIMIT 1
                if txn is None: TRANSACTION ABORT
                select * from transactions where payment_id=payment_id and kind=kind
                TRANSACTION COMMIT
                
    TRANSACTION COMMIT
    """
    txn = []

    checkout = Checkout()
    txn.append(f"r-{checkout_pk}")
    if not checkout.exists:
        txn.append(f"r-order{checkout_pk}")
        return txn
    
    payment = Payment()
    txn.append(f"r-{payment.id}")
    try:
        if payment.to_confirm:
            txn.append(f"r-ACTION_TO_CONFIRM")
        response = np.random.binomial(1, 0.5)
        if response:
            txn.append(f"w-{payment.id}")
        gateway_response = np.random.binomial(1, 0.5)
        if gateway_response:
            txn.append(f"r-TRANSACTION")
    except:
        txn = complete_checkout_fail_handler(checkout, payment, txn)

    if not payment.is_active:
        txn = complete_checkout_fail_handler(checkout, payment, txn)
    return txn

def complete_checkout_fail_handler(checkout: Checkout, payment: Payment, txn: list[str]) -> list[str]:
    update_fields = []
    if checkout.completing_started_at is not None:
        update_fields.append("completing_started_at")
    
    voucher = Voucher()
    if voucher.exists:
        if not checkout.is_voucher_usage_increased:
            pass
        else:
            if not update_fields:
                txn.append(f"w-is_voucher_usage_increased")
            else:
                update_fields.append("is_voucher_usage_increased")
            if voucher.usage_limit:
                txn.append(f"w-{voucher.usage_limit - 1}")
            if voucher.single_use:
                txn.append(f"w-{False}")
            if voucher.apply_once_per_customer:
                txn.append(f"w-{voucher.apply_once_per_customer}")
    if update_fields:
        txn.append(f"w-checkout")
    
    if payment:
        if payment.can_refund:
            txn.append(f"r-refund")
            if txn is None:
                return txn
            txn.append(f"r-refund")
        elif payment.can_void:
            txn.append(f"r-void")
            if txn is None:
                return txn
            txn.append(f"r-void")   
    return txn


def saleor_checkout_payment_process_sim():
    """
    Example output;

    ['r-13', 'r-80', 'r-ACTION_TO_CONFIRM']
    ['r-0', 'r-order0']
    ['r-16', 'r-19']
    ['r-30', 'r-31', 'w-31', 'r-TRANSACTION', 'r-void', 'r-void']
    ['r-54', 'r-95']
    ['r-35', 'r-71', 'r-TRANSACTION', 'r-refund', 'r-refund']
    ['r-72', 'r-61', 'r-TRANSACTION', 'w-checkout', 'r-void', 'r-void']
    ['r-41', 'r-order41']
    ['r-58', 'r-70', 'r-ACTION_TO_CONFIRM', 'w-70']
    ['r-67', 'r-96', 'w-96', 'r-TRANSACTION']
    """
    checkout_pks = list(range(100))
    num_txn = 10
    for _ in range(num_txn):
        checkout_pk = np.random.choice(checkout_pks)
        result = saleor_checkout_payment_process_generator(checkout_pk)
        print(result)

def main():
    # saleor_checkout_voucher_code_sim()
    saleor_checkout_payment_process_sim()

if __name__ == '__main__':
    main()
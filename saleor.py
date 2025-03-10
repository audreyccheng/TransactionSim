# https://github.com/saleor/saleor
# Uses PostgreSQL
# Found in Tang et al. Ad Hoc Transactions in Web Applications: The Good, the Bad, and the Ugly

# Contextual note: select_for_update is used to lock rows until the end of the transaction. 
# Django docs: https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update 

import numpy as np

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
    voucher_ids = list(range(100))

    class Voucher: 
        def __init__(self):
            self.is_voucher_usage_increased = np.random.binomial(1, 0.5)
            self.usage_limit = np.random.normal(5, 1)
            self.apply_once_per_customer = np.random.binomial(1, 0.5)
            self.single_use = np.random.binomial(1, 0.5)
    
    class Code:
        def __init__(self):
            self.used = np.random.choice(range(10))
            self.is_active = np.random.binomial(1, 0.5)
            self.voucher_id = np.random.choice(voucher_ids)
    
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

    ['r-60', 'r-98', 'r-60', 'w-9']
    ['r-47', 'r-63', 'r-47', 'w-2', 'w-63']
    ['r-83', 'r-53']
    ['r-78', 'r-23', 'r-78', 'w-2', 'w-23']
    ['r-4', 'r-76', 'r-4', 'w-3']
    ['r-64', 'r-21', 'r-64', 'w-4', 'w-False']
    ['r-45', 'r-59', 'r-45', 'w-4', 'w-59']
    ['r-60', 'r-37', 'r-60', 'w-3', 'w-37']
    """
    voucher_codes = list(range(100))
    num_txn = 100
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

def saleor_checkout_payment_process():
    """
    Transaction 16
    Purpose: Coordinate concurrent checkout.
    saleor/checkout/complete_checkout.py#complete_checkout(with payment to process)
    https://github.com/saleor/saleor/blob/27eed6e93f79a73b81cf97465ba8552b66d31c40/saleor/checkout/complete_checkout.py#L1754-L1791 
    https://github.com/saleor/saleor/blob/2ee9490104e6b256899d90adcde9f7bdfbcecfe1/saleor/payment/gateway.py#L261 ?
    """

def main():
    saleor_checkout_voucher_code_sim()

if __name__ == '__main__':
    main()
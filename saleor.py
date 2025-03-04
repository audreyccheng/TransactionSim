# https://github.com/saleor/saleor
# Uses PostgreSQL
import numpy as np

def saleor_checkout_voucher_code():
    """
    Transaction 1
    Purpose: Coordinate concurrent checkout.
    saleor/checkout/complete_checkout.py#complete_checkout(with voucher code usage)
    https://github.com/saleor/saleor/blob/main/saleor/checkout/complete_checkout.py get_voucher_for_checkout_info called (two places) in 
        #1 _process_voucher_data_for_order called in _prepare_order_data in _get_order_data in _prepare_checkout_with_payment in complete_checkout_pre_payment_part in complete_checkout_with_payment in complete_checkout

        #2 _increase_voucher_code_usage_value in create_order_from_checkout in complete_checkout_with_transaction in complete_checkout
    https://github.com/saleor/saleor/blob/main/saleor/checkout/utils.py get_voucher_for_checkout
    Summary of get_voucher_for_checkout function: 
    1.	Initial Check for Voucher Code: If a voucher code is provided in the checkout object, the code searches for a corresponding VoucherCode from the database.
	2.	Voucher Validation: Depending on whether checkout.is_voucher_usage_increased is True, it either directly fetches the voucher or performs additional filtering with a channel-specific validation (active_in_channel).
	3.	Prefetching: If with_prefetch is True, it prefetches related objects for the voucher to optimize subsequent queries.
	4.	***Locking: If the voucher has a usage limit and with_lock is True, the function applies a lock on the VoucherCode using select_for_update to ensure no concurrent modification of the voucher code during the transaction.

    select_for_update is used to lock rows until the end of the transaction. Django docs: https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update 

    Inputs to transaction: voucher.usage_limit and with_lock affect whether this transaction runs. If run, the transaction gets the checkout.voucher_code

    Focusing on #2: get_voucher_for_checkout_info in _increase_voucher_code_usage_value in create_order_from_checkout in complete_checkout_with_transaction in complete_checkout
    https://github.com/saleor/saleor/blob/2ee9490104e6b256899d90adcde9f7bdfbcecfe1/saleor/checkout/complete_checkout.py#L1127 
    PSEUDOCODE: 
    In: checkout_info
    TRANSACTION START
    ** get_voucher_for_checkout part
    if checkout_info.voucher_code is not None:
        code = Select * from voucher_codes where code=checkout_info.voucher_code and is_active=True
        if code DNE: TRANSACTION ABORT??
        if checkout_info.is_voucher_usage_increased:
            voucher = Select * from vouchers where id=code.voucher_id LIMIT 1
        else:
            voucher = Select * from vouchers where id=code.voucher_id and active_in_channel=checkout_info.channel_id LIMIT 1????
    
    if not voucher: TRANSACTION ABORT

    if voucher.usage_limit and with_lock:
        code = Select * from voucher_codes where code=checkout_info.voucher_code FOR UPDATE

    ** _increase_checkout_voucher_usage part
    if voucher.usage_limit: # increase_voucher_code_usage_value
        (with transaction.atomic): from voucher_codes set usage=usage+1 where code=checkout_info.voucher_code
    if voucher.apply_once_per_customer and increase_voucher_customer_usage: # add_voucher_usage_by_customer
        if not customer_email: TRANSACTION ABORT
        created = Get_or_create from voucher_customer where voucher_id=code and customer_email=customer_email
        if not created: TRANSACTION ABORT
    if voucher.single_use: # deactivate_voucher_code
        (with transaction.atomic) from voucher_codes set is_active=False where code=checkout_info.voucher_code

    TRANSACTION COMMIT

    Note that second part uses the save function: https://github.com/saleor/saleor/blob/2ee9490104e6b256899d90adcde9f7bdfbcecfe1/saleor/core/models.py#L31

    
    Example pseudocode:
    In: item_id
    TRANSACTION START
    alloc := Select * from allocations where item_id = item_id FOR UPDATE
    stock := Select * from stocks where id=alloc.stock_id FOR UPDATE
    if alloc.qty > stock.qty: TRANSACTION ABORT
    else
        Update allocations Set qty=0 Where id=alloc.id
        Update stocks Set qty=qty-alloc.qty Where id=stock.id
        TRANSACTION COMMIT

    TODO: no mention in paper of distribution. What % of transactions use voucher codes?
    """
    pass

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
    pass

if __name__ == '__main__':
    main()